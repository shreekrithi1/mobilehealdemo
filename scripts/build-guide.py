#!/usr/bin/env python3
"""Build the dependency-free codelab from its Markdown source."""
import html
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / 'codelab'


def inline(text):
    text = html.escape(text)
    stash = []
    def code(m):
        stash.append('<code>' + m[1] + '</code>')
        return f'@@CODE{len(stash)-1}@@'
    text = re.sub(r'`([^`]+)`', code, text)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
    for i, value in enumerate(stash):
        text = text.replace(f'@@CODE{i}@@', value)
    return text


def render(markdown):
    lines = markdown.strip().splitlines()
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1; continue
        if line.startswith('```'):
            lang = line[3:] or 'text'; body = []; i += 1
            while i < len(lines) and not lines[i].startswith('```'):
                body.append(lines[i]); i += 1
            out.append('<div class="codeblock"><div class="codebar"><span>' + html.escape(lang) + '</span><button class="copy" type="button" aria-label="Copy code">Copy</button></div><pre><code>' + html.escape('\n'.join(body)) + '</code></pre></div>')
            i += 1; continue
        image = re.fullmatch(r'!\[([^\]]+)\]\(([^)]+)\)', line)
        if image:
            out.append('<figure><button class="image-open" type="button" aria-label="Enlarge screenshot"><img loading="lazy" src="' + html.escape(image[2]) + '" alt="' + html.escape(image[1]) + '"></button></figure>')
            i += 1; continue
        heading = re.match(r'^(#{2,4}) (.+)', line)
        if heading:
            n = len(heading[1]); out.append(f'<h{n}>' + inline(heading[2]) + f'</h{n}>'); i += 1; continue
        if line.startswith('> '):
            body = []
            while i < len(lines) and lines[i].startswith('> '):
                body.append(lines[i][2:]); i += 1
            out.append('<aside class="callout">' + inline(' '.join(body)) + '</aside>'); continue
        if re.match(r'^(?:- |\d+\. )', line):
            ordered = not line.startswith('- '); tag = 'ol' if ordered else 'ul'; items = []
            pattern = r'^\d+\. ' if ordered else r'^- '
            while i < len(lines) and re.match(pattern, lines[i]):
                items.append('<li>' + inline(re.sub(pattern, '', lines[i])) + '</li>'); i += 1
            out.append(f'<{tag}>' + ''.join(items) + f'</{tag}>'); continue
        body = [line]; i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r'^(?:#|>|```|!\[|- |\d+\. )', lines[i]):
            body.append(lines[i]); i += 1
        out.append('<p>' + inline(' '.join(body)) + '</p>')
    return '\n'.join(out)


def main():
    source = (GUIDE / 'guide.md').read_text()
    parts = re.split(r'<!-- step: (.+?) \| (\d+) \| (.+?) -->', source)
    steps = []
    for i in range(1, len(parts), 4):
        title, minutes, group, body = parts[i:i+4]
        steps.append(dict(title=title, minutes=int(minutes), group=group, html=render(body)))
    (GUIDE / 'steps.json').write_text(json.dumps(steps, ensure_ascii=False, indent=2) + '\n')
    print(f'Built {len(steps)} lessons from guide.md')


if __name__ == '__main__':
    main()
