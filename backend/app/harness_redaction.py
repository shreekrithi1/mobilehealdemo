"""Conservative recursive sanitization for provider and audit boundaries."""
import re
from collections.abc import Mapping

MARKER = '[REDACTED]'
_SECRET_NAMES = r'(?:secret|token|password|passwd|authorization|credential|api.?key|private.?key|cookie|email|phone|ssn)'
_SECRET_KEY = re.compile(_SECRET_NAMES, re.I)
_PATTERNS = [
    re.compile(r'-----BEGIN [\w ]*PRIVATE KEY-----.*?(?:-----END [\w ]*PRIVATE KEY-----|\Z)', re.S),
    re.compile(r'(?i)\bBearer\s+[^\s,;]+'),
    # Quoted keys (JSON) and quoted values must be consumed as a whole, including
    # escaped quotes and whitespace. Unterminated quoted values redact to EOF.
    re.compile(
        r'''(?:["'][^"'\r\n]*''' + _SECRET_NAMES + r'''[^"'\r\n]*["']|[\w.-]*'''
        + _SECRET_NAMES + r'''[\w.-]*)\s*[:=]\s*(?:"(?:\\.|[^"\\])*(?:"|\Z)|'(?:\\.|[^'\\])*(?:'|\Z)|[^\s,;}]+)''', re.I),
    re.compile(r'(?i)https?://[^\s/@:]+:[^\s/@]+@'),
    re.compile(r'\b(?:sk-[A-Za-z0-9_-]{8,}|gh[pousr]_[A-Za-z0-9_]+|AKIA[A-Z0-9]{16})\b'),
    re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'),
    re.compile(r'(?<!\w)(?:\+?\d{1,3}[ .-]?)?(?:\(\d{3}\)|\d{3})[ .-]?\d{3}[ .-]?\d{4}(?!\w)'),
    re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
]


def redact(value: object) -> object:
    """Copy nested values without preserving unknown objects' sensitive reprs."""
    if isinstance(value, Mapping):
        return {str(redact(str(k))): MARKER if _SECRET_KEY.search(str(k)) else redact(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [redact(v) for v in value]
    if isinstance(value, str):
        for pattern in _PATTERNS:
            value = pattern.sub(MARKER, value)
        return value
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return MARKER
