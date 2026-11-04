#!/usr/bin/env python3
"""
Render info-card.svg: focus areas orbiting a glowing core (depth-scaled, comet trails, starfield),
stack logos on two tilted inner rings, a "now" line that decrypts itself on a loop and a pinging open-to-work status.
CSS + SMIL only, both of which GitHub plays inside <img>.
  python3 scripts/card.py
"""
import html
import os
import random
import re
import urllib.request

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "info-card.svg")
NOW = "Software Engineer @ 3C Solutions"
EMPLOYER = "3C Solutions"  # highlighted once decrypted
FOCUS = [("Web", "#22d3ee"), ("Mobile", "#39d353"), ("Desktop", "#bc8cff"), ("AI Automation", "#f2cc60"), ("UI/UX Design", "#f778ba")]
SI = "https://cdn.jsdelivr.net/npm/simple-icons@16.36.0/icons/{}.svg"  # CC0 brand paths, 24x24
STACK = [  # inner rings: (tilt deg, s per lap, reverse, [(simple-icons slug, colour on dark)])
    (32, 22, False, [("react", "#61dafb"), ("nextdotjs", "#e6edf3"), ("vuedotjs", "#4fc08d"), ("angular", "#dd0031"), ("laravel", "#ff2d20")]),
    (-32, 28, True, [("typescript", "#3178c6"), ("flutter", "#54c5f8"), ("electron", "#9feaf9"), ("tailwindcss", "#06b6d4"), ("figma", "#f24e1e")]),
]
MODES = ["on-site", "hybrid", "remote"]

W, H = 490, 388  # 490 wide renders ~388 tall next to the 370-wide portrait
CX, CY, RX, RY = 245, 146, 172, 50  # orbit
LAP = 18  # s per orbit
GLYPHS = "!<>-_/[]{}=+*^?#$%&01"
FRAMES, FRAME_S, CYCLE, DECRYPT_AT = 18, 0.055, 9.0, 1.3
VX, NOW_Y, STATUS_Y = 110, 266, 304
BG, BG2, FRAME, MUTED, INK, CYAN, GREEN = "#0d1117", "#111722", "#30363d", "#7d8590", "#c9d1d9", "#22d3ee", "#39d353"
random.seed(7)


def ring(rx, ry):
    """Ellipse as four quarter arcs from the front point, so each quarter is exactly 1/4 of a lap."""
    a = f"A{rx},{ry} 0 0 0"
    return f"M{CX},{CY + ry} {a} {CX + rx},{CY} {a} {CX},{CY - ry} {a} {CX - rx},{CY} {a} {CX},{CY + ry}"


ORBIT = ring(RX, RY)
# front -> side -> back -> side -> front; cos-shaped depth = ease-in, ease-out, ease-in, ease-out
DEPTH = 'keyTimes="0;.25;.5;.75;1" calcMode="spline" keySplines=".5 0 1 1;0 0 .5 1;.5 0 1 1;0 0 .5 1"'

stars = []
while len(stars) < 26:
    x, y = random.uniform(12, W - 12), random.uniform(38, 222)
    if abs(x - CX) < 64 and abs(y - CY) < 56 or x < 80 and y < 68:  # keep clear of the core and the key
        continue
    stars.append(f'<circle class="tw" cx="{x:.0f}" cy="{y:.0f}" r="{random.uniform(.5, 1.2):.1f}" fill="{INK}" opacity=".5" '
                 f'style="animation-duration:{random.uniform(2.5, 6):.1f}s;animation-delay:{random.uniform(0, 3):.1f}s"/>')

symbols, rings, logos = [], [], []
for ang, lap, rev, stack in STACK:
    path = ring(116, 32)
    rings.append(f'<path class="draw" transform="rotate({ang} {CX} {CY})" d="{path}" pathLength="1" fill="none" stroke="{FRAME}"/>')
    for k, (slug, color) in enumerate(stack):
        d = re.search(r'<path d="([^"]+)"', urllib.request.urlopen(SI.format(slug)).read().decode())[1]
        symbols.append(f'<symbol id="{slug}" viewBox="0 0 24 24"><path d="{d}"/></symbol>')
        t = f'dur="{lap}s" begin="-{lap * k / len(stack):g}s" repeatCount="indefinite"'
        back = ' keyPoints="1;0" keyTimes="0;1" calcMode="linear"' if rev else ""
        logos.append(f'<g class="in" style="animation-delay:{1.2 + .08 * k:.2f}s" transform="rotate({ang} {CX} {CY})"><g>'
                     f'<animateMotion {t}{back} path="{path}"/><g transform="rotate({-ang})"><g>'
                     f'<animateTransform attributeName="transform" type="scale" values="1;.78;.58;.78;1" {DEPTH} {t}/>'
                     f'<animate attributeName="opacity" values="1;.75;.45;.75;1" {DEPTH} {t}/>'
                     f'<circle r="10" fill="#161b22" stroke="{color}" stroke-opacity=".45"/>'
                     f'<use href="#{slug}" x="-6" y="-6" width="12" height="12" fill="{color}"/></g></g></g></g>')

trails, nodes = [], []
for k, (name, color) in enumerate(FOCUS):
    for length, width, op in ((34, 3, .1), (18, 2, .25), (7, 2, .6)):  # stacked dashes fake a fading tail
        d0 = length - 100 * k / len(FOCUS)
        trails.append(f'<path d="{ORBIT}" pathLength="100" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" '
                      f'opacity="{op}" stroke-dasharray="{length} {100 - length}" stroke-dashoffset="{d0:g}">'
                      f'<animate attributeName="stroke-dashoffset" from="{d0:g}" to="{d0 - 100:g}" dur="{LAP}s" repeatCount="indefinite"/></path>')
    t = f'dur="{LAP}s" begin="-{LAP * k / len(FOCUS):g}s" repeatCount="indefinite"'
    nodes.append(f'<g class="in" style="animation-delay:{.9 + .12 * k:.2f}s"><g><animateMotion {t} path="{ORBIT}"/><g>'
                 f'<animateTransform attributeName="transform" type="scale" values="1;.78;.58;.78;1" {DEPTH} {t}/>'
                 f'<animate attributeName="opacity" values="1;.7;.4;.7;1" {DEPTH} {t}/>'
                 f'<circle r="11" fill="{color}" opacity=".2"/><circle r="4.5" fill="{color}"/>'
                 f'<text class="lab" y="-15" text-anchor="middle" fill="{color}">{html.escape(name)}</text></g></g></g>')


def window(a, b=None):
    """Discrete opacity window [a, b) seconds into each decrypt cycle."""
    if b is None:
        vals, kt = "0;1", f"0;{a / CYCLE:.4f}"
    elif a == 0:
        vals, kt = "1;0", f"0;{b / CYCLE:.4f}"
    else:
        vals, kt = "0;1;0", f"0;{a / CYCLE:.4f};{b / CYCLE:.4f}"
    return f'<animate attributeName="opacity" values="{vals}" keyTimes="{kt}" calcMode="discrete" dur="{CYCLE}s" begin="{DECRYPT_AT}s" repeatCount="indefinite"/>'


def runs(chars):
    """[(char, class)] -> tspans, merging neighbours with the same class."""
    out, cur, buf = [], None, ""
    for ch, cls in chars + [("", None)]:
        if cls != cur and buf:
            out.append(f'<tspan class="{cur}">{html.escape(buf)}</tspan>')
            buf = ""
        cur, buf = cls, buf + ch
    return "".join(out)


emp = NOW.index(EMPLOYER)
final = runs([(ch, "b" if j >= emp else "m" if ch == "@" else "v") for j, ch in enumerate(NOW)])
resolve = [int(j / len(NOW) * FRAMES * .7 + random.random() * FRAMES * .3) for j in range(len(NOW))]
frames = []
for i in range(FRAMES):
    chars = [(ch, "v") if i > resolve[j] or ch == " " else (random.choice(GLYPHS), "g") for j, ch in enumerate(NOW)]
    frames.append(f'<text x="{VX}" y="{NOW_Y}" opacity="0">{window(i * FRAME_S, (i + 1) * FRAME_S)}{runs(chars)}</text>')
frames.append(f'<text x="{VX}" y="{NOW_Y}" opacity="0">{window(FRAMES * FRAME_S)}{final}</text>')

chips, x = [], 234
for k, mode in enumerate(MODES):
    w = len(mode) * 6.7 + 18
    shape = f'<rect x="{x:.1f}" y="291" width="{w:.1f}" height="19" rx="9.5"'
    label = f'<text x="{x + w / 2:.1f}" y="304.5" font-size="11" text-anchor="middle"'
    chips.append(f'{shape} fill="#161b22" stroke="{FRAME}"/>{label} fill="{MUTED}">{mode}</text>'
                 f'<g class="chip" style="animation-delay:{2.6 + 1.5 * k:g}s">{shape} fill="{GREEN}" fill-opacity=".14" stroke="{GREEN}"/>'
                 f'{label} fill="{GREEN}">{mode}</text></g>')
    x += w + 6

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="13">
<style>
.k{{fill:{CYAN};font-weight:700}}.v{{fill:{INK}}}.m{{fill:{MUTED}}}.g{{fill:{CYAN};opacity:.75}}.b{{fill:#e6edf3;font-weight:700}}
.lab{{font-size:12px;font-weight:600;paint-order:stroke;stroke:{BG};stroke-width:3px;stroke-linejoin:round}}
.o{{transform-origin:{CX}px {CY}px}}
.in{{animation:in .6s ease-out backwards}}
.pop{{animation:pop .8s .2s cubic-bezier(.2,1.5,.4,1) backwards}}
.halo{{animation:br 4s ease-in-out infinite}}
.spin{{animation:spin 14s linear infinite}}.rspin{{animation:spin 24s linear infinite reverse}}
.wave{{animation:wave 4s .35s ease-out infinite backwards}}
.draw{{stroke-dasharray:1;animation:draw 1.4s .4s cubic-bezier(.6,0,.2,1) backwards}}
.tw{{animation:tw 4s ease-in-out infinite backwards}}
.ping{{transform-box:fill-box;transform-origin:center;animation:ping 2s ease-out infinite backwards}}
.chip{{animation:chip 4.5s infinite backwards}}
.scan{{animation:scan 7s linear infinite}}
.still{{display:none}}
@keyframes in{{from{{opacity:0;transform:translateY(6px)}}}}
@keyframes pop{{from{{transform:scale(0)}}}}
@keyframes br{{50%{{transform:scale(1.2);opacity:.55}}}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
@keyframes wave{{from{{transform:scale(1);opacity:.7}}70%,to{{transform:scale(5.5);opacity:0}}}}
@keyframes draw{{from{{stroke-dashoffset:1}}}}
@keyframes tw{{0%,100%{{opacity:.12}}50%{{opacity:.9}}}}
@keyframes ping{{from{{transform:scale(1);opacity:.9}}to{{transform:scale(4.5);opacity:0}}}}
@keyframes chip{{0%,100%{{opacity:0}}6%,36%{{opacity:1}}46%{{opacity:0}}}}
@keyframes scan{{from{{transform:translateY(0)}}to{{transform:translateY({H + 60}px)}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}.scr,.wave,.scan{{display:none}}.still{{display:inline}}}}
</style>
<defs>
<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient>
<linearGradient id="band" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{CYAN}" stop-opacity="0"/><stop offset=".85" stop-color="{CYAN}" stop-opacity=".06"/><stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></linearGradient>
<linearGradient id="fade" gradientUnits="userSpaceOnUse" x1="0" y1="{CY - RY}" x2="0" y2="{CY + RY}"><stop offset="0" stop-color="#fff" stop-opacity=".3"/><stop offset="1" stop-color="#fff"/></linearGradient>
<mask id="depth"><rect width="{W}" height="{H}" fill="url(#fade)"/></mask>
<radialGradient id="halo"><stop offset="0" stop-color="{CYAN}" stop-opacity=".45"/><stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></radialGradient>
<radialGradient id="orb" fx=".35" fy=".3"><stop offset="0" stop-color="#ecfeff"/><stop offset=".3" stop-color="{CYAN}"/><stop offset=".75" stop-color="#1f6feb"/><stop offset="1" stop-color="#0b3a8a"/></radialGradient>
<pattern id="dots" width="16" height="16" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r=".8" fill="#1b2230"/></pattern>
{"".join(symbols)}
<clipPath id="card"><rect width="{W}" height="{H}" rx="12"/></clipPath>
</defs>
<rect width="{W}" height="{H}" rx="12" fill="url(#bg)"/>
<g clip-path="url(#card)"><rect y="31" width="{W}" height="{H - 31}" fill="url(#dots)"/><rect class="scan" y="-60" width="{W}" height="60" fill="url(#band)"/></g>
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="12" fill="none" stroke="{FRAME}"/>
<line x1="0" y1="30" x2="{W}" y2="30" stroke="{FRAME}"/>
<circle cx="20" cy="15" r="5" fill="#ff5f56"/><circle cx="36" cy="15" r="5" fill="#ffbd2e"/><circle cx="52" cy="15" r="5" fill="#27c93f"/>
<text x="{W / 2:g}" y="19" fill="{MUTED}" font-size="12" text-anchor="middle">albertirgi@github: ~$ ./status.sh</text>

{chr(10).join(stars)}
<text class="k in" style="animation-delay:.2s" x="24" y="58">Focus</text>
{chr(10).join(rings)}
<path class="draw" d="{ORBIT}" pathLength="1" fill="none" stroke="#58a6ff" stroke-opacity=".5" mask="url(#depth)"/>
<g class="in" style="animation-delay:.9s" mask="url(#depth)">
{chr(10).join(trails)}
</g>
<g class="pop o">
<circle class="halo o" cx="{CX}" cy="{CY}" r="52" fill="url(#halo)"/>
<circle class="spin o" cx="{CX}" cy="{CY}" r="33" fill="none" stroke="{CYAN}" stroke-opacity=".5" stroke-dasharray="3 6"/>
<circle class="rspin o" cx="{CX}" cy="{CY}" r="39" fill="none" stroke="{CYAN}" stroke-opacity=".25" stroke-dasharray="18 10 2 10"/>
<circle cx="{CX}" cy="{CY}" r="24" fill="url(#orb)"/>
<text x="{CX}" y="{CY + 3}" fill="{BG}" font-size="8.5" font-weight="800" letter-spacing="1.2" text-anchor="middle">FOCUS</text>
</g>
<circle class="wave o" cx="{CX}" cy="{CY}" r="24" fill="none" stroke="{CYAN}" vector-effect="non-scaling-stroke"/>
{chr(10).join(logos)}
{chr(10).join(nodes)}

<line class="in" style="animation-delay:1.1s" x1="24" y1="232" x2="{W - 24}" y2="232" stroke="#21262d"/>
<text class="k in" style="animation-delay:1.2s" x="24" y="{NOW_Y}">Now</text>
<g class="scr" xml:space="preserve">
{chr(10).join(frames)}
</g>
<text class="still" x="{VX}" y="{NOW_Y}" xml:space="preserve">{final}</text>
<g class="in" style="animation-delay:2.2s">
<text class="k" x="24" y="{STATUS_Y}">Status</text>
<circle class="ping" style="animation-delay:2.2s" cx="{VX + 6}" cy="{STATUS_Y - 4.5}" r="4" fill="none" stroke="{GREEN}"/>
<circle class="ping" style="animation-delay:3.2s" cx="{VX + 6}" cy="{STATUS_Y - 4.5}" r="4" fill="none" stroke="{GREEN}"/>
<circle cx="{VX + 6}" cy="{STATUS_Y - 4.5}" r="4" fill="{GREEN}"/>
<text x="{VX + 18}" y="{STATUS_Y}" fill="{GREEN}" font-weight="700">open to work</text>
{chr(10).join(chips)}
</g>
<text class="m in" style="animation-delay:2.8s" x="24" y="360">albertirgi@github:~$</text>
<rect x="186" y="349" width="8" height="14" fill="{INK}" opacity="0"><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" dur="1s" begin="3.2s" repeatCount="indefinite"/></rect>
</svg>
'''

with open(OUT, "w") as f:
    f.write(svg)
print(f"wrote {os.path.normpath(OUT)}")
