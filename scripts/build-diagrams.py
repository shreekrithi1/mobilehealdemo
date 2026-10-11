#!/usr/bin/env python3
"""Generate the animated, Google-style SVG diagrams used by the codelab.

Each diagram runs on one loop (CYCLE seconds). A packet travels each connector in its
own time slot and each card lights up in its Google colour when the packet arrives, so
the flow builds left to right and then resets. app.js pauses the animation (showing the
finished state) for people who prefer reduced motion and wires the Pause/Replay button.
"""
from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / 'codelab' / 'diagrams'
BLUE, RED, YELLOW, GREEN = '#1a73e8', '#d93025', '#f9ab00', '#1e8e3e'
TINT = {BLUE: '#e8f0fe', RED: '#fce8e6', YELLOW: '#fef7e0', GREEN: '#e6f4ea'}
GREY, INK, MUTED = '#dadce0', '#202124', '#5f6368'
CYCLE = 12.0


def kt(t):
    return f'{max(0.0, min(1.0, t)):.4f}'


class Svg:
    def __init__(self, w, h, title, desc):
        self.w, self.h, self.parts = w, h, []
        self.title, self.desc = title, desc

    def add(self, s):
        self.parts.append(s)

    def lit(self, el_attr, start, base, color):
        """Animate an attribute from base → color at `start` (0..1 of the cycle), hold, reset at the end."""
        a = min(start + 0.035, 0.93)
        return (f'<animate attributeName="{el_attr}" dur="{CYCLE}s" repeatCount="indefinite" calcMode="spline" '
                'keySplines="0 0 1 1;0.22 1 0.36 1;0 0 1 1;0.4 0 0.2 1" '
                f'values="{base};{base};{color};{color};{base}" keyTimes="0;{kt(start)};{kt(a)};0.96;1"/>')

    def card(self, x, y, w, h, color, num, title, sub='', owner='', start=0.0, icon=None):
        tint = TINT[color]
        s = [f'<g class="card"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="#fff" stroke="{GREY}" stroke-width="1.5">',
             self.lit('stroke', start, GREY, color), self.lit('fill', start, '#ffffff', tint), '</rect>']
        cx, cy = x + 30, y + 32
        s.append(f'<circle cx="{cx}" cy="{cy}" r="17" fill="{tint}">{self.lit("fill", start, tint, color)}</circle>')
        s.append(f'<text x="{cx}" y="{cy + 5}" text-anchor="middle" class="num" fill="{color}">{escape(str(icon or num))}'
                 f'{self.lit("fill", start, color, "#ffffff")}</text>')
        s.append(f'<text x="{x + 58}" y="{y + 30}" class="t">{escape(title)}</text>')
        if sub:
            s.append(f'<text x="{x + 58}" y="{y + 49}" class="s">{escape(sub)}</text>')
        if owner:
            ow = 14 + 6.3 * len(owner)
            s.append(f'<g class="owner"><rect x="{x + 58}" y="{y + h - 26}" width="{ow:.0f}" height="18" rx="9" fill="#f1f3f4"/>'
                     f'<text x="{x + 66}" y="{y + h - 13}" class="o">{escape(owner)}</text></g>')
        s.append('</g>')
        self.add(''.join(s))

    def wire(self, d, start, end, color=BLUE, dashed=False, label='', lx=0, ly=0, arrow=True):
        dash = ' stroke-dasharray="6 6"' if dashed else ''
        self.add(f'<path d="{d}" fill="none" stroke="{GREY}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"{dash}'
                 f'{" marker-end=\"url(#ah)\"" if arrow else ""}/>')
        # coloured trail that draws itself during the slot
        self.add(f'<path d="{d}" pathLength="100" fill="none" stroke="{color}" stroke-width="3" stroke-linecap="round" '
                 f'stroke-linejoin="round" stroke-dasharray="100 100" stroke-dashoffset="100">'
                 f'<animate attributeName="stroke-dashoffset" dur="{CYCLE}s" repeatCount="indefinite" calcMode="linear" '
                 f'values="100;100;0;0;100" keyTimes="0;{kt(start)};{kt(end)};0.96;1"/></path>')
        self.add(f'<circle r="6" fill="{color}" class="pkt" opacity="0">'
                 f'<animate attributeName="opacity" dur="{CYCLE}s" repeatCount="indefinite" values="0;0;1;1;0;0" '
                 f'keyTimes="0;{kt(start)};{kt(start + 0.005)};{kt(end - 0.005)};{kt(end)};1"/>'
                 f'<animateMotion dur="{CYCLE}s" repeatCount="indefinite" calcMode="linear" path="{d}" '
                 f'keyPoints="0;0;1;1" keyTimes="0;{kt(start)};{kt(end)};1"/></circle>')
        if label:
            self.add(f'<text x="{lx}" y="{ly}" class="lbl">{escape(label)}</text>')

    def render(self, name):
        head = (f'<svg class="dg" data-cycle="{CYCLE}" viewBox="0 0 {self.w} {self.h}" role="img" aria-labelledby="{name}-t {name}-d" '
                f'xmlns="http://www.w3.org/2000/svg"><title id="{name}-t">{escape(self.title)}</title>'
                f'<desc id="{name}-d">{escape(self.desc)}</desc>'
                f'<style>text{{font-family:"Google Sans",Roboto,Arial,sans-serif}}.t{{font-size:15px;font-weight:500;fill:#202124}}'
                f'.h{{font-size:17px;font-weight:500;fill:#202124}}.s{{font-size:12px;fill:#5f6368}}.s2{{font-size:13px;fill:#3c4043}}'
                f'.o{{font-size:11px;font-weight:500;fill:#3c4043}}.num{{font-size:14px;font-weight:700}}.lbl{{font-size:11.5px;fill:#5f6368;font-style:italic}}'
                f'.gate{{font-size:11px;font-weight:500;fill:#b06000}}</style>'
                f'<defs><marker id="ah" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
                f'<path d="M0 0L10 5L0 10z" fill="#9aa0a6"/></marker></defs>')
        OUT.mkdir(exist_ok=True)
        (OUT / f'{name}.svg').write_text(head + '\n'.join(self.parts) + '</svg>\n')


def slots(n, lo=0.04, hi=0.86):
    step = (hi - lo) / n
    return [(lo + i * step, lo + i * step + step * 0.8) for i in range(n)]


def architecture():
    g = Svg(960, 600, 'MobileHeal architecture',
            'A business user works in the web portal; the portal and the Android and iOS apps call the FastAPI backend. '
            'Inside it, Delivery workflow, Crash healer, DataWatchdog and the Agent council share one workspace. '
            'Changes land in an isolated Git workspace and state in a SQLite database. GitHub, Jira, Figma and Crashlytics '
            'are optional integrations, simulated in demo mode.')
    s = slots(6)
    g.add(f'<rect x="150" y="186" width="580" height="236" rx="20" fill="#f8f9fa" stroke="{GREY}" stroke-width="1.5"/>'
          f'<text x="174" y="218" class="h">FastAPI backend</text><text x="320" y="218" class="s">localhost:8000 · a crew that keeps apps healthy</text>')
    g.add(f'<rect x="770" y="186" width="170" height="236" rx="20" fill="#fff" stroke="{GREY}" stroke-width="1.5" stroke-dasharray="6 6"/>'
          f'<text x="790" y="218" class="h">Integrations</text><text x="790" y="238" class="s">simulated in demo mode</text>')
    for i, (name, c) in enumerate([('GitHub / GitLab', INK), ('Jira', BLUE), ('Figma', RED), ('Crashlytics', YELLOW)]):
        y = 268 + i * 38
        g.add(f'<circle cx="800" cy="{y - 5}" r="7" fill="{c}"/><text x="816" y="{y}" class="s2">{name}</text>')
    g.wire('M250 78 H360', *s[0], BLUE, label='requests · approvals', lx=258, ly=66)
    g.wire('M470 124 V186', *s[1], BLUE, label='REST API', lx=480, ly=160)
    g.wire('M820 124 V150 H640 V186', *s[1], GREEN, label='API + WebSocket', lx=660, ly=144)
    g.card(30, 34, 220, 90, BLUE, 1, 'Business user', 'writes requirements', 'Product owner', s[0][0], icon='👤')
    g.card(360, 34, 230, 90, BLUE, 2, 'Web portal', 'requests · reviews · Crashlytics', 'localhost:8000', s[1][0], icon='▣')
    g.card(690, 34, 250, 90, GREEN, 3, 'Android + iOS', 'Kotlin · SwiftUI clients', 'live updates', s[1][0], icon='▯')
    agents = [(BLUE, 'Delivery workflow', 'ideas → tested PRs', '⇄'), (RED, 'Crash healer', 'finds & patches crashes', '✚'),
              (GREEN, 'DataWatchdog', 'keeps records healthy', '◉'), (YELLOW, 'Agent council', '7 roles · RCA · opinions', '★')]
    for i, (c, t, sub, ic) in enumerate(agents):
        x, y = 170 + (i % 2) * 275, 240 + (i // 2) * 88
        g.card(x, y, 260, 74, c, i + 1, t, sub, '', s[2][0] + i * 0.03, icon=ic)
    g.wire('M730 304 H770', *s[3], YELLOW, dashed=True)
    g.wire('M305 422 V478', *s[4], BLUE, label='branches + code', lx=315, ly=456)
    g.wire('M580 422 V478', *s[4], GREEN, label='profiles + workflow state', lx=590, ly=456)
    g.card(170, 478, 270, 84, BLUE, 1, 'Isolated Git workspace', 'main · feature/heal-123', 'safe sandbox', s[4][1], icon='⑂')
    g.card(450, 478, 270, 84, GREEN, 2, 'SQLite database', 'persistent demo state', 'local only', s[4][1], icon='⛁')
    g.add(f'<text x="480" y="590" text-anchor="middle" class="s">✓ Human approvals guard design, tests, merge and the production switch</text>')
    g.render('architecture')


def delivery():
    g = Svg(960, 520, 'Delivery workflow and recovery loop',
            'Six stages: Requirements, UX design (human approval), Code, Pull request (review approvals), Tests, Merge '
            '(release decision). Below, the recovery loop: a crash or data issue is detected and diagnosed, a fix is '
            'proposed and enters delivery as a pull request, it is reviewed and verified, then the failing request is replayed.')
    stages = [('Requirements', 'rules from plain English', BLUE, ''), ('UX design', 'before / after', RED, 'Human approval'),
              ('Code', 'branch + tests', YELLOW, ''), ('Pull request', 'diff + checks', BLUE, 'Review approvals'),
              ('Tests', 'unit · UI · edge', GREEN, ''), ('Merge', 'main · Figma sync', GREEN, 'Release decision')]
    n = len(stages)
    s = slots(n + 5, 0.03, 0.9)
    xs = [20 + i * 158 for i in range(n)]
    W = 132
    for i in range(n - 1):
        g.wire(f'M{xs[i] + W} 82 H{xs[i + 1]}', *s[i], stages[i + 1][2])
    for i, (t, sub, c, gate) in enumerate(stages):
        g.card(xs[i], 40, W, 84, c, i + 1, t, '', '', s[i - 1][1] if i else 0.02)
        g.add(f'<text x="{xs[i] + 14}" y="{40 + 70}" class="s">{escape(sub)}</text>')
        if gate:
            g.add(f'<g><rect x="{xs[i] + 6}" y="138" width="120" height="26" rx="13" fill="#fef7e0" stroke="#f9ab00"/>'
                  f'<text x="{xs[i] + 66}" y="155" text-anchor="middle" class="gate">🔒 {escape(gate)}</text></g>')
    g.add(f'<rect x="20" y="222" width="920" height="270" rx="20" fill="#f8f9fa" stroke="{GREY}" stroke-width="1.5"/>'
          f'<text x="44" y="256" class="h">The recovery loop</text>'
          f'<text x="210" y="256" class="s">crashes and data issues come back through the same reviewed path</text>')
    loop = [('Issue', 'crash or bad data', RED, '!'), ('Diagnose', 'logs · root cause', BLUE, '?'), ('Propose fix', 'patch + test', YELLOW, '✚'),
            ('Verify', 'review · re-test', BLUE, '✓'), ('Replay', 'or rescan data', GREEN, '↻')]
    lx = [44 + i * 180 for i in range(5)]
    base = n - 1
    for i in range(4):
        g.wire(f'M{lx[i] + 150} 318 H{lx[i + 1]}', *s[base + i], loop[i + 1][2])
    for i, (t, sub, c, ic) in enumerate(loop):
        g.card(lx[i], 280, 150, 76, c, i + 1, t, sub, '', s[base + i - 1][1] if i else s[base][0], icon=ic)
    g.wire('M845 356 V440 H119 V356', s[-1][0], 0.95, GREEN, dashed=True, label='fixed — keep watching', lx=420, ly=432)
    g.wire(f'M{lx[2] + 75} 280 V206 H{xs[2] + 66} V124', *s[base + 1], YELLOW, dashed=True,
           label='fix enters delivery as a PR', lx=lx[2] + 84, ly=200)
    g.render('delivery')


def enterprise():
    g = Svg(960, 600, 'Enterprise incident-to-production flow',
            'A Crashlytics crash is picked up by the monitor agent, which logs an incident. The seven-agent council writes the '
            'root-cause analysis. A requirement gap becomes a change request; a defect goes straight to the fix. Design, code, '
            'a pull request with checks, and review by two agents in Autopilot or two humans in Manual mode follow. The PR '
            'waits, ready to deploy, until a person flips the human-in-the-loop switch to release to production.')
    s = slots(10, 0.03, 0.9)
    xs = [20, 260, 500, 740]
    row1 = [('Crash detected', 'Firebase Crashlytics', 'Monitor bot', RED, '⚡'),
            ('Incident logged', 'severity · stack · device', 'SRE on-call', RED, '!'),
            ('Council RCA', '7 agents · 5 whys', 'Eng. manager', YELLOW, '★'),
            ('Change request', 'if requirement gap', 'Product manager', BLUE, '✎')]
    row2 = [('Design', 'before / after · a11y', 'UX designer', RED, '◐'),
            ('Code', 'branch · tests · fix', 'Engineer', YELLOW, '</>'),
            ('PR + checks', 'build · tests · scan', 'QA lead', BLUE, '⑂'),
            ('PR review', '2 agents · or 2 humans', 'Reviewers', GREEN, '✓✓')]
    for i in range(3):
        g.wire(f'M{xs[i] + 200} 98 H{xs[i + 1]}', *s[i], row1[i + 1][3])
    g.wire(f'M840 136 V196 H130 V250', *s[3], row2[0][3])
    g.add(f'<path d="M600 136 V176 H110" fill="none" stroke="{GREY}" stroke-width="2" stroke-dasharray="4 6"/>'
          f'<text x="300" y="170" class="lbl">defect → straight to the fix</text>')
    for i in range(3):
        g.wire(f'M{xs[i] + 200} 288 H{xs[i + 1]}', *s[4 + i], row2[i + 1][3])
    g.wire('M840 326 V392 H470 V430', *s[7], GREEN)
    for i, (t, sub, o, c, ic) in enumerate(row1):
        g.card(xs[i], 60, 200, 96, c, i + 1, t, sub, o, s[i - 1][1] if i else 0.02, icon=ic)
    for i, (t, sub, o, c, ic) in enumerate(row2):
        g.card(xs[i], 250, 200, 96, c, i + 5, t, sub, o, s[3 + i][1], icon=ic)
    # human-in-the-loop switch
    t0, t1 = s[8]
    g.add(f'<g><rect x="330" y="430" width="280" height="110" rx="16" fill="#fff" stroke="{GREY}" stroke-width="1.5">'
          f'{g.lit("stroke", t1, GREY, GREEN)}</rect>'
          f'<text x="352" y="462" class="t">Human-in-the-loop switch</text><text x="352" y="482" class="s">PR is ready to deploy · waits for you</text>'
          f'<rect x="352" y="498" width="64" height="30" rx="15" fill="#bdc1c6">{g.lit("fill", t1, "#bdc1c6", GREEN)}</rect>'
          f'<circle cx="367" cy="513" r="11" fill="#fff"><animate attributeName="cx" dur="{CYCLE}s" repeatCount="indefinite" '
          f'values="367;367;401;401;367" keyTimes="0;{kt(t0 + 0.02)};{kt(t1)};0.96;1"/></circle>'
          f'<text x="428" y="518" class="o">Release manager</text></g>')
    g.wire('M610 485 H680', *s[9], GREEN)
    g.card(680, 440, 260, 96, GREEN, 10, 'Production', 'merged to main · deployed', 'Live', s[9][1], icon='🚀')
    g.add(f'<rect x="20" y="430" width="290" height="110" rx="16" fill="#e8f0fe"/>'
          f'<text x="40" y="460" class="t">Autopilot</text><text x="40" y="480" class="s">a bot owns every step · 2 reviewer agents</text>'
          f'<text x="40" y="508" class="t">Manual</text><text x="40" y="528" class="s">the owners above · 2 human approvers</text>')
    g.add(f'<text x="480" y="580" text-anchor="middle" class="s">The production switch always stays with a person.</text>')
    g.render('enterprise')


if __name__ == '__main__':
    architecture(); delivery(); enterprise()
    print('Wrote', ', '.join(p.name for p in sorted(OUT.glob('*.svg'))))
