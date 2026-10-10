"""Host-owned named tools. Context/registry are trusted application inputs, never model data."""
from __future__ import annotations
import fnmatch
import math
import os
import selectors
import signal
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import MappingProxyType
from typing import Callable
from .harness_models import EvidenceItem
from .harness_redaction import redact


class ToolPermissionError(ValueError):
    pass


def resolve_allowed_path(root: Path, relative: str, allowed_paths: list[str]) -> Path:
    if not isinstance(relative, str) or not relative or '\\' in relative or '\x00' in relative:
        raise ToolPermissionError('Invalid path')
    path = Path(relative)
    if path.is_absolute() or '..' in path.parts:
        raise ToolPermissionError('Workspace escape denied')
    lowered = [p.lower() for p in path.parts]
    forbidden = {'.git', '.aws', '.ssh', '.codex', '.agents', 'agents.md', 'skill.md', 'harness_policy.py', 'guardrails.md', 'threat-model.md'}
    if any(p in forbidden or p.startswith('.env') or any(s in p for s in ('credential', 'secret', 'policy')) or p.endswith(('.pem', '.key', '.p12', '.keystore')) for p in lowered):
        raise ToolPermissionError('Protected path denied')
    root = Path(root).resolve(strict=True)
    candidate = root / path
    # Reject symlinks even when their current target is contained: avoid aliasing protected files.
    cursor = root
    for part in path.parts:
        cursor /= part
        if cursor.is_symlink():
            raise ToolPermissionError('Symlink paths denied')
    resolved = candidate.resolve()
    if not resolved.is_relative_to(root):
        raise ToolPermissionError('Workspace escape denied')
    if not any(isinstance(pattern, str) and fnmatch.fnmatchcase(path.as_posix(), pattern) for pattern in allowed_paths):
        raise ToolPermissionError('Path outside configured allowlist')
    return resolved


@dataclass(frozen=True)
class ToolSpec:
    executable: str
    build_argv: Callable[[dict, dict], list[str]]
    permission: str = 'read'
    mutation: bool = False
    external: bool = False
    timeout: float = 300
    output_cap: int = 65536
    argument_names: frozenset[str] = frozenset()
    # No isolated runtime is bundled. Arbitrary/native tools remain unavailable.
    # Only host-owned known commands may explicitly accept process-group cleanup,
    # which cannot contain descendants that detach into a new session.
    requires_isolation: bool = True


def _no_args(arguments, context):
    return []


DEFAULT_REGISTRY = {
    'git_status': ToolSpec('git', lambda a,c: ['--no-optional-locks', 'status', '--short'], requires_isolation=False),
    'git_diff': ToolSpec('git', lambda a,c: ['--no-pager', 'diff', '--no-ext-diff', '--no-textconv'], requires_isolation=False),
}


class ToolExecutor:
    def __init__(self, registry: dict[str, ToolSpec] | None = None):
        self.registry = MappingProxyType(dict(DEFAULT_REGISTRY if registry is None else registry))
        for spec in self.registry.values():
            if not isinstance(spec, ToolSpec) or not math.isfinite(spec.timeout) or not 0 < spec.timeout <= 3600 or not isinstance(spec.output_cap, int) or not 1 <= spec.output_cap <= 1048576:
                raise ValueError('Invalid host tool limits')
            if Path(spec.executable).name in {'sh', 'bash', 'zsh', 'fish', 'cmd', 'powershell'}:
                raise ValueError('Shell tools are forbidden')

    def execute(self, tool_name: str, arguments: dict, context: dict) -> EvidenceItem:
        spec = self.registry.get(tool_name)
        if spec is None:
            raise ToolPermissionError('Unknown tool')
        if not isinstance(arguments, dict) or set(arguments) - spec.argument_names:
            raise ToolPermissionError('Unsupported tool arguments')
        if spec.permission not in context.get('permissions', ()):
            raise ToolPermissionError('Tool permission denied')
        if spec.external and (context.get('demo_mode', True) or not context.get('external_authorized', False)):
            raise ToolPermissionError('External action denied')
        if spec.mutation and not context.get('mutation_authorized', False):
            raise ToolPermissionError('Mutation authorization required')
        if spec.requires_isolation:
            return EvidenceItem(id=f'tool:{tool_name}', category='verification', status='unavailable',
                revision=context['revision'], commit=context['commit'], source=f'tool:{tool_name}',
                timestamp=datetime.now(timezone.utc), summary='Required process isolation runtime unavailable; tool was not launched',
                duration_seconds=0)
        root = Path(context['root']).resolve(strict=True)
        argv = [spec.executable, *spec.build_argv(dict(arguments), context)]
        if any(not isinstance(arg, str) or '\x00' in arg for arg in argv):
            raise ToolPermissionError('Malformed argv')
        cancel = context.get('cancel_event')
        started = time.monotonic()
        status, summary, code = 'failed', '', None
        captured = bytearray()
        truncated = False
        process = None
        try:
            if cancel is not None and cancel.is_set():
                summary = 'cancelled before execution'
            else:
                # No provider credentials or user shell hooks inherited by tools.
                env = {k: os.environ[k] for k in ('PATH', 'LANG', 'TMPDIR', 'SYSTEMROOT') if k in os.environ}
                env.update({'GIT_TERMINAL_PROMPT': '0', 'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull})
                process = subprocess.Popen(argv, cwd=root, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True)
                selector = selectors.DefaultSelector()
                selector.register(process.stdout, selectors.EVENT_READ)
                try:
                    while True:
                        if cancel is not None and cancel.is_set():
                            summary = 'cancelled'
                            break
                        if time.monotonic() - started >= spec.timeout:
                            summary = 'timeout'
                            break
                        ready = selector.select(0.05)
                        if ready:
                            chunk = os.read(process.stdout.fileno(), 8192)
                            if not chunk:
                                if process.poll() is not None:
                                    break
                            else:
                                remaining = spec.output_cap - len(captured)
                                captured.extend(chunk[:remaining])
                                truncated |= len(chunk) > remaining
                        elif process.poll() is not None:
                            # Drain any bytes still buffered in the pipe.
                            continue
                finally:
                    selector.close()
                if not summary:
                    code = process.wait(timeout=1)
                    status = 'passed' if code == 0 else 'failed'
        except FileNotFoundError:
            status, summary = 'unavailable', 'Executable unavailable'
        except (OSError, subprocess.SubprocessError) as error:
            summary = f'Tool execution failed: {redact(str(error))}'
        finally:
            if process is not None:
                # Kill members remaining in the group; detached descendants require
                # a real isolated runtime and are not covered by this host opt-out.
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
                code = process.returncode
                process.stdout.close()
        output = str(redact(captured.decode('utf-8', errors='replace')))
        summary = str(redact(summary)) + ('\n' if summary and output else '') + output
        if truncated:
            summary += '\n[output truncated]'
        return EvidenceItem(id=f'tool:{tool_name}', category='verification', status=status,
            revision=context['revision'], commit=context['commit'], source=f'tool:{tool_name}',
            timestamp=datetime.now(timezone.utc), summary=summary, command=redact(argv),
            exit_code=code, duration_seconds=time.monotonic()-started)
