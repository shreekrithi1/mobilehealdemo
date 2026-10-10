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
        diagram = re.fullmatch(r'\{\{diagram (\w+)\}\}', line.strip())
        if diagram:
            svg = (GUIDE / 'diagrams' / (diagram[1] + '.svg')).read_text().strip()
            out.append('<figure class="diagram">' + svg + '<div class="dg-bar"><span class="dg-live"><span class="dg-dot"></span>Animated</span>'
                       '<button class="dg-toggle" type="button" aria-pressed="false">Pause</button>'
                       '<button class="dg-replay" type="button">Replay</button></div></figure>')
            i += 1; continue
        image = re.fullmatch(r'!\[([^\]]+)\]\(([^)]+)\)', line)
        if image:
            label = 'Enlarge diagram' if 'mobileheal-' in image[2] else 'Enlarge screenshot'
            out.append('<figure><button class="image-open" type="button" aria-label="' + label + '"><img loading="lazy" src="' + html.escape(image[2]) + '" alt="' + html.escape(image[1]) + '"></button></figure>')
            i += 1; continue
        if line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?', c) for c in cells):
                    rows.append(cells)
                i += 1
            head = '<tr>' + ''.join('<th>' + inline(c) + '</th>' for c in rows[0]) + '</tr>'
            body = ''.join('<tr>' + ''.join('<td>' + inline(c) + '</td>' for c in r) + '</tr>' for r in rows[1:])
            out.append('<div class="table-wrap"><table>' + head + body + '</table></div>'); continue
        if line.strip() == '---':
            out.append('<hr>'); i += 1; continue
        heading = re.match(r'^(#{1,4}) (.+)', line)
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
        while i < len(lines) and lines[i].strip() and not re.match(r'^(?:#|>|```|!\[|\{\{|\||---$|- |\d+\. )', lines[i]):
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
    build_pages()


TOP = '<header class="topbar"><a class="brand" href="index.html#0"><span class="brandmark" aria-hidden="true">⌁</span><span>MobileHeal <span class="brand-label">CODELAB</span></span></a>{links}</header>'


def menu(active):
    items = [('index.html#0', 'Tutorial'), ('demos.html', 'Demos'), ('pitch.html', 'Pitch')]
    links = ''.join(f'<a href="{h}"' + (' aria-current="page"' if n == active else '') + f'>{n}</a>' for h, n in items)
    return ('<nav class="mainnav" aria-label="Main">' + links + '</nav><div class="toplinks"><a id="open-app" href="http://localhost:8000/#new" target="_blank" rel="noopener">Open demo <span aria-hidden="true">↗</span></a>'
            '<a href="https://github.com/shreekrithi1/mobilehealdemo" target="_blank" rel="noopener">Source <span aria-hidden="true">↗</span></a></div>')


def page(title, active, body, extra=''):
    fonts = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
             '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&display=swap">'
             '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&family=Roboto+Mono:wght@400;500&family=DM+Sans:wght@400;500;700&display=swap">')
    return ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>{html.escape(title)} · MobileHeal</title>{fonts}<link rel="stylesheet" href="styles.css"></head>'
            f'<body class="page-{active.lower()}">' + TOP.format(links=menu(active)) + body + extra + '</body></html>\n')


def build_pages():
    demos = render((ROOT / 'docs' / 'DEMOS.md').read_text())
    (GUIDE / 'demos.html').write_text(page('Demo scripts', 'Demos', '<main class="solo"><article id="lesson">' + demos + '</article></main>',
        '<script>document.querySelectorAll(".copy").forEach(b=>b.onclick=async()=>{try{await navigator.clipboard.writeText(b.closest(".codeblock").querySelector("code").textContent);b.textContent="Copied ✓"}catch(e){}})</script>'))
    order = json.loads((GUIDE / 'pitch' / 'order.json').read_text())
    slides = ''.join('<div class="slide-frame"><div class="slide-scale">' + re.sub(r'<aside>.*?</aside>', '', (GUIDE / 'pitch' / f'{s}.html').read_text(), flags=re.S) + '</div></div>' for s in order)
    body = ('<main class="solo pitch"><div class="pitch-head"><h2>Self-Healing Software</h2><span id="pcount"></span>'
            '<button id="pprev" type="button">← Prev</button><button id="pnext" type="button">Next →</button><button id="pfull" type="button">Present</button></div>'
            '<div id="deck">' + slides + '</div></main>')
    js = ('<script>(()=>{const deck=document.getElementById("deck"),fr=[...deck.children];let i=0;'
          'const fit=()=>fr.forEach(f=>{const s=f.querySelector(".slide-scale");s.style.transform="scale("+(f.clientWidth/1920)+")"});'
          'const show=n=>{i=Math.max(0,Math.min(fr.length-1,n));fr.forEach((f,k)=>f.classList.toggle("on",k===i));document.getElementById("pcount").textContent=(i+1)+" / "+fr.length;fit()};'
          'document.getElementById("pprev").onclick=()=>show(i-1);document.getElementById("pnext").onclick=()=>show(i+1);'
          'document.getElementById("pfull").onclick=()=>deck.requestFullscreen&&deck.requestFullscreen();'
          'deck.onclick=()=>show(i+1);addEventListener("keydown",e=>{if(e.key==="ArrowRight"||e.key===" ")show(i+1);if(e.key==="ArrowLeft")show(i-1)});'
          'addEventListener("resize",fit);document.addEventListener("fullscreenchange",()=>setTimeout(fit,50));show(0)})()</script>')
    (GUIDE / 'pitch.html').write_text(page('Pitch', 'Pitch', body, js))


if __name__ == '__main__':
    main()
