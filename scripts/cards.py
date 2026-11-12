#!/usr/bin/env python3
"""
Render every profile card in cards/ as an animated SVG: cream cards, Instrument Serif + Geist,
fonts inlined as base64 because GitHub's <img> can't load external fonts. CSS + SMIL only, both of
which GitHub plays. Stdlib only; run daily by .github/workflows/update-cards.yml.
  GITHUB_TOKEN=$(gh auth token) python3 scripts/cards.py
The hero's ASCII portrait comes from cards/portrait.txt (scripts/portrait.py).
"""
import base64
import datetime
import functools
import html
import json
import math
import os
import random
import re
import sys
import urllib.request

USER = "albertirgi"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cards")

ROLE = "Software Engineer at 3C Solutions"
FIRST, LAST = "Albert", "Irgi"
TAGLINE = ["I build for web, mobile and desktop,", "and automate the rest with AI."]
SITE = "albertirgi.com"
BUILD = ["web apps", "mobile apps", "desktop apps", "AI automation", "UI/UX design"]
LAND = "https://cdn.jsdelivr.net/gh/nvkelso/natural-earth-vector@v5.1.2/geojson/ne_110m_land.geojson"
FEATURED = "replica"
INSTALL = "npx skills add albertirgi/replica"

INK, MUTED, BODY, CREAM, RULE, GREY = "#111111", "#6e6e73", "#3a3a3c", "#f3f3f1", "#dcdcd7", "#c9c9c4"
BLUE, RED, YELLOW = "#2f55ff", "#ef3b2d", "#ffc81a"
LEVELS = ["#e2e2de", "#c8d3ff", "#94a8ff", "#2f55ff", "#1a3be0"]  # github data-level 0..4
SERIF = "'Instrument Serif', Georgia, serif"
SANS = "Geist, system-ui, -apple-system, sans-serif"
MONO = "'Geist Mono', ui-monospace, SFMono-Regular, Menlo, monospace"
FONTS = [  # (embed when the card contains this, @font-face descriptors, fontsource file)
    (SERIF, "font-family:'Instrument Serif';font-style:normal", "instrument-serif@5.2.8/latin-400-normal"),
    (SERIF, "font-family:'Instrument Serif';font-style:italic", "instrument-serif@5.2.8/latin-400-italic"),
    (SANS, "font-family:'Geist';font-weight:400", "geist@5.2.8/latin-400-normal"),
    ('font-weight="600"', "font-family:'Geist';font-weight:600", "geist@5.2.8/latin-600-normal"),
    (MONO, "font-family:'Geist Mono'", "geist-mono@5.2.8/latin-400-normal"),
]
CSS = (
    "@keyframes rise{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}"
    "@keyframes fade{from{opacity:0}to{opacity:1}}"
    "@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}"
    "@keyframes pop{0%{opacity:0;transform:scale(.3)}70%{opacity:1;transform:scale(1.15)}100%{opacity:1;transform:none}}"
    "@keyframes pulse{0%,100%{opacity:1}50%{opacity:.25}}"
    "@keyframes nudge{0%,100%{transform:none}50%{transform:translateX(4px)}}"
    "@keyframes nudgeup{0%,100%{transform:none}50%{transform:translate(3px,-3px)}}"
    "@keyframes tilein{0%{opacity:0;transform:translateY(90px) scale(.6) rotate(-9deg)}55%{opacity:1;transform:translateY(-10px) scale(1.05) rotate(2deg)}"
    "75%{transform:translateY(3px) scale(.98) rotate(-.8deg)}90%{transform:translateY(-1px) scale(1.01) rotate(.2deg)}100%{opacity:1;transform:none}}"
    "@keyframes roll{from{transform:translateY(60px)}to{transform:none}}"
    "@keyframes sheen{0%{transform:translateX(-260px) skewX(-20deg)}22%,100%{transform:translateX(420px) skewX(-20deg)}}"
    "@keyframes ring{0%{opacity:.7;transform:scale(.2)}100%{opacity:0;transform:scale(2.4)}}"
    "@keyframes growx{from{transform:scaleX(0)}to{transform:scaleX(1)}}"
    ".gx{transform-box:fill-box;transform-origin:left;transform:scaleX(0);animation:growx .9s cubic-bezier(.2,.7,.2,1) both}"
    ".r{opacity:0;animation:rise .8s cubic-bezier(.2,.7,.2,1) both;transform-box:fill-box}"
    ".f{opacity:0;animation:fade .9s ease-out both}"
    ".g{transform-box:fill-box;transform-origin:bottom;transform:scaleY(0);animation:grow .8s cubic-bezier(.2,.7,.2,1) both}"
    ".p{opacity:0;transform-box:fill-box;transform-origin:center;animation:pop .4s ease-out both}"
    ".live{animation:pulse 1.6s ease-in-out infinite}"
    ".n{transform-box:fill-box;animation:nudge 1.8s ease-in-out infinite}"
    ".nu{transform-box:fill-box;animation:nudgeup 1.8s ease-in-out infinite}"
    ".ti{opacity:0;transform-box:fill-box;transform-origin:50% 60%;animation:tilein 1.1s cubic-bezier(.2,.8,.2,1) both}"
    ".ro{transform-box:fill-box;animation:roll .8s cubic-bezier(.15,.8,.2,1) both}"
    ".sh{animation:sheen 5s ease-in-out infinite}"
    ".rg{opacity:0;transform-box:fill-box;transform-origin:center;animation:ring 1s ease-out both}"
    "@media (prefers-reduced-motion:reduce){.r,.f,.g,.gx,.p,.live,.n,.nu,.ti,.ro{animation:none!important;opacity:1!important;"
    "transform:none!important}.sh,.rg{display:none}}"
)
e = html.escape


def get(url):
    headers = {"User-Agent": "profile-cards"}
    if "api.github.com" in url and os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    return urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30).read()


@functools.lru_cache(None)
def font(file):
    return base64.b64encode(get(f"https://cdn.jsdelivr.net/fontsource/fonts/{file}.woff2")).decode()


def svg(name, w, h, label, body):
    faces = "".join(f"@font-face{{{desc};src:url(data:font/woff2;base64,{font(file)}) format('woff2')}}"
                    for needle, desc, file in FONTS if needle in body)
    label = e(label)
    with open(os.path.join(OUT, f"{name}.svg"), "w") as f:
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.3f}" height="{h}" viewBox="0 0 {w:.3f} {h}" role="img" '
                f'aria-label="{label}"><title>{label}</title><style>{faces}{CSS}</style>{body}</svg>')


def t(x, y, s, family, size, fill, extra=""):
    return f'<text x="{x:g}" y="{y:g}" font-family="{family}" font-size="{size}" fill="{fill}"{extra}>{s}</text>'


def delay(s, cls):
    return f' class="{cls}" style="animation-delay:{s:.2f}s"'


def big(lead, word):  # "976 <i>contributions</i>"
    return f'{e(str(lead))} <tspan font-style="italic">{e(word)}</tspan>'


def count(n, word, begin, x, y, size, fill):
    """Number that counts up to n (ease-out), one SMIL-swapped frame per step."""
    vals = [round(n * (1 - (1 - k / 14) ** 3)) for k in range(15)]
    out = []
    for k, v in enumerate(vals):
        t0 = begin + k * 0.06
        hide = "" if k == 14 else f'<set attributeName="opacity" to="0" begin="{t0 + 0.06:.3f}s"/>'
        out.append(t(x, y, big(f"{v:,}", word) + f'<set attributeName="opacity" to="1" begin="{t0:.3f}s"/>{hide}',
                     SERIF, size, fill, ' opacity="0"'))
    return "".join(out)


def wave(f, k=24):
    """One full turn of f(angle) as a SMIL values list; elements share it and differ only by a negative begin."""
    return ";".join(f(2 * math.pi * j / k) for j in range(k + 1))


def fetch_days():
    page = get(f"https://github.com/users/{USER}/contributions").decode()
    cells = {}
    for td in re.findall(r"<td[^>]*ContributionCalendar-day[^>]*>", page):
        date, cid, lvl = (re.search(rf'{a}="([^"]*)"', td) for a in ("data-date", "id", "data-level"))
        if date and cid:
            cells[cid.group(1)] = {"date": date.group(1), "level": int(lvl.group(1)) if lvl else 0, "count": 0}
    for cid, text in re.findall(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]*)</tool-tip>', page):
        m = re.match(r"(\d[\d,]*)", text)
        if cid in cells and m:
            cells[cid]["count"] = int(m.group(1).replace(",", ""))
    if not cells:
        sys.exit("no calendar cells found -- github markup may have changed")
    return sorted(cells.values(), key=lambda d: d["date"])


def streaks(counts):
    """(current, longest) run of non-zero days; today still counts as pending while it is zero."""
    run = best = 0
    for c in counts:
        run = run + 1 if c else 0
        best = max(best, run)
    c = counts[:-1] if counts and not counts[-1] else counts
    cur = next((i for i, v in enumerate(reversed(c)) if not v), len(c))
    return cur, best


def hero(rows):
    cell_h = 800 / len(rows[0]) * 15 / 8  # matches portrait.py's glyph aspect
    s = min(360 / 800, 360 / (len(rows) * cell_h))  # fits a 360px square, right-aligned
    tx, ty = 846 - 800 * s, 30 + (360 - len(rows) * cell_h * s) / 2
    art = "".join(
        f'<text class="f" style="animation-delay:{0.25 + i * 0.018:.3f}s;animation-duration:.35s" xml:space="preserve" '
        f'x="0" y="{i * cell_h + cell_h * 0.74:.1f}" fill="{INK}" font-size="{cell_h * 0.86:.1f}" '
        f'textLength="800" lengthAdjust="spacing">{e(row)}</text>'
        for i, row in enumerate(rows) if row.strip())
    body = (
        '<defs><linearGradient id="shine" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="600" y2="0">'
        f'<stop offset="0" stop-color="{INK}"/><stop offset=".42" stop-color="{INK}"/><stop offset=".5" stop-color="{BLUE}"/>'
        f'<stop offset=".58" stop-color="{INK}"/><stop offset="1" stop-color="{INK}"/>'
        '<animateTransform attributeName="gradientTransform" type="translate" values="-600 0;600 0;600 0" '
        'keyTimes="0;.45;1" dur="7s" begin="1.6s" repeatCount="indefinite"/></linearGradient></defs>'
        f'<rect width="880" height="420" rx="14" fill="{CREAM}"/>'
        f'<g{delay(0, "f")}><rect class="live" x="48" y="49" width="8" height="8" rx="2" fill="{BLUE}"/>'
        + t(66, 57, e(ROLE.upper()), MONO, 12, MUTED, ' letter-spacing="1"') + "</g>"
        + t(44, 190, e(FIRST), SERIF, 116, INK, delay(0.15, "r") + ' letter-spacing="-2.5"')
        + t(44, 290, e(LAST), SERIF, 116, "url(#shine)", delay(0.3, "r") + ' font-style="italic" letter-spacing="-2.5"')
        + f'<g{delay(0.55, "r")}>' + "".join(t(48, 338 + 27 * i, e(line), SANS, 18, BODY) for i, line in enumerate(TAGLINE)) + "</g>"
        + f'<g{delay(0.8, "f")}>' + t(48, 396, e(SITE), MONO, 13, INK)
        + t(48 + len(SITE) * 7.8 + 10, 396, "&#8599;", MONO, 13, BLUE, ' class="nu"') + "</g>"
        + f'<g transform="translate({tx:.1f} {ty:.1f}) scale({s:.4f})" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-weight="700">{art}</g>'
    )
    svg("hero", 880, 432, f"{FIRST} {LAST}. {ROLE}. {' '.join(TAGLINE)}", body)


def heatmap(days):
    first = datetime.date.fromisoformat(days[0]["date"])
    cols = [[None] * ((first.weekday() + 1) % 7)]  # sunday = row 0
    for d in days:
        if len(cols[-1]) == 7:
            cols.append([])
        cols[-1].append(d)
    total = sum(d["count"] for d in days)
    p = [f'<rect width="880" height="245" rx="14" fill="{CREAM}"/>',
         t(42, 62, f'A year <tspan font-style="italic" fill="{BLUE}">in blue</tspan>', SERIF, 34, INK, delay(0.8, "r")),
         t(836, 60, "REFRESHED DAILY", MONO, 12, MUTED, delay(0.8, "f") + ' text-anchor="end" letter-spacing="1"')]
    prev = None
    for ci, col in enumerate(cols):
        x = 44 + ci * 15
        for ri, d in enumerate(col):
            if d:
                s = "" if d["count"] == 1 else "s"
                p.append(f'<rect{delay(1 + ci * 0.015 + ri * 0.02, "p")} x="{x}" y="{96 + ri * 15}" width="12" height="12" rx="3" '
                         f'fill="{LEVELS[d["level"]]}"><title>{d["date"]}: {d["count"]:,} contribution{s}</title></rect>')
        date = datetime.date.fromisoformat(next(c for c in col if c)["date"])
        if date.month != prev and (prev or date.day <= 7) and x < 700:  # skip a partial first month and the legend
            p.append(t(x, 217, f"{date:%b}", MONO, 11, MUTED))
        prev = date.month
    p.append(f'<g{delay(1.6, "f")}>' + t(758, 217, "less", MONO, 11, MUTED, ' text-anchor="end"')
             + "".join(f'<rect x="{766 + i * 14}" y="207" width="11" height="11" rx="2.5" fill="{c}"/>' for i, c in enumerate(LEVELS))
             + t(838, 217, "more", MONO, 11, MUTED) + "</g>")
    svg("heatmap", 880, 257, f"Contribution graph: {total:,} contributions in the last year", "".join(p))


def activity(days):
    total = sum(d["count"] for d in days)
    months = {}
    for d in days:
        months[d["date"][:7]] = months.get(d["date"][:7], 0) + d["count"]
    keys = sorted(months)[-12:]
    peak, top = max(keys, key=months.get), max(months[k] for k in keys) or 1
    p = [f'<rect width="880" height="340" rx="14" fill="{CREAM}"/>',
         t(40, 58, "THE LAST 12 MONTHS ON GITHUB", MONO, 12, MUTED, delay(1.9, "f") + ' letter-spacing="1"'),
         f'<g{delay(2, "r")}>{count(total, "contributions", 2, 38, 114, 52, INK)}</g>']
    for i, k in enumerate(keys):
        v, x, at = months[k], 40 + i * 47.5, 2.2 + i * 0.07
        h = max(4, round(140 * v / top))
        fill = BLUE if k == peak else GREY if i == len(keys) - 1 else INK  # last month is still running
        name = datetime.date(int(k[:4]), int(k[5:]), 1).strftime("%b")
        p.append(f'<rect{delay(at, "g")} x="{x:.1f}" y="{292 - h}" width="37.5" height="{h}" rx="{min(4, h / 2):g}" fill="{fill}">'
                 f'<title>{name}: {v:,}</title></rect>'
                 + t(x + 18.75, 314, name, MONO, 11, MUTED, delay(at, "f") + ' text-anchor="middle"'))
        if k == peak:
            p.append(t(x + 18.75, 282 - h, f"{v:,}", MONO, 11, BLUE, delay(3.2, "p") + ' text-anchor="middle"'))
    counts = [d["count"] for d in days]
    cur, best = streaks(counts)
    note = ("current streak, and the longest" if cur and cur == best
            else f"longest streak, {cur} running now" if cur else "longest streak")
    active = sum(1 for c in counts if c)
    stats = [(big(best, "day" if best == 1 else "days"), note),
             (f'{active:,}<tspan fill="#8e8e93"> / {len(counts):,}</tspan>', "days with a commit"),
             (f"{max(counts):,}", "on the busiest day")]
    for i, (num, cap) in enumerate(stats):
        y = 104 + i * 92
        p.append(f'<g{delay(2.6 + i * 0.15, "r")}>' + t(650, y, num, SERIF, 40, INK) + t(650, y + 24, e(cap), SANS, 13, MUTED) + "</g>")
        if i < 2:
            p.append(f'<rect{delay(2.6, "f")} x="650" y="{y + 44}" width="190" height="1" fill="{RULE}"/>')
    svg("activity", 880, 352, f"{total:,} contributions in the last year, {best}-day longest streak", "".join(p))


TILE_W = 880 / 3 - 8


def land_dots(step=5):
    """{lon: [lat, ...]} on a step-degree grid where Natural Earth has land; rows thin out toward the poles."""
    polys = []
    for f in json.loads(get(LAND))["features"]:
        ring = f["geometry"]["coordinates"][0]  # 110m land is all simple polygons
        xs, ys = [q[0] for q in ring], [q[1] for q in ring]
        polys.append((min(xs), max(xs), min(ys), max(ys), ring))

    def inside(x, y):
        for x0, x1, y0, y1, ring in polys:
            if x0 <= x <= x1 and y0 <= y <= y1:
                hit = False
                for (ax, ay), (bx, by) in zip(ring, ring[1:]):  # rings are closed
                    if (ay > y) != (by > y) and x < ax + (y - ay) * (bx - ax) / (by - ay):
                        hit = not hit
                if hit:
                    return True
        return False

    land = {}
    for lat in range(-55, 80, step):
        every = max(1, round(1 / math.cos(math.radians(lat))))
        for k, lon in enumerate(range(-180, 180, step)):
            if k % every == 0 and inside(lon, lat):
                land.setdefault(lon, []).append(lat)
    return land


def globe(land, ink, pin, cx, cy, r=66, spin_s=48, home=(-8.4, 115.2), face=141.2):
    """Dotted earth turning in place. Each meridian is one path scaled on x by sin(angle), so dots follow the
    sphere while non-scaling strokes keep them round; the far side shows faintly. Home (Bali) gets a pulsing pin;
    face is the longitude in front when the card loads, so home drifts through the middle as the tile lands."""
    sx = wave(lambda a: f"{math.sin(a):.3f} 1")
    fade = wave(lambda a: f"{0.14 + 0.86 * max(0.0, math.cos(a)) ** 0.7:.2f}")

    def spin(lon):
        return f'dur="{spin_s}s" begin="-{spin_s * ((lon - face) % 360) / 360:.2f}s" repeatCount="indefinite"'

    p = ['<defs><radialGradient id="halo" cx=".38" cy=".32"><stop offset="0" stop-color="#fff" stop-opacity=".22"/>'
         '<stop offset=".75" stop-color="#fff" stop-opacity=".04"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient></defs>',
         f'<circle cx="{cx:.1f}" cy="{cy}" r="{r}" fill="url(#halo)" stroke="{ink}" stroke-opacity=".25"/>']
    for lon, lats in sorted(land.items()):
        d = "".join(f"M{r * math.cos(math.radians(lat)):.1f} {cy - r * math.sin(math.radians(lat)):.1f}h0" for lat in lats)
        p.append(f'<g transform="translate({cx:.1f} 0)"><g><animateTransform attributeName="transform" type="scale" values="{sx}" {spin(lon)}/>'
                 f'<animate attributeName="opacity" values="{fade}" {spin(lon)}/><path d="{d}" stroke="{ink}" stroke-width="2.6" '
                 'stroke-linecap="round" vector-effect="non-scaling-stroke"/></g></g>')
    lat, lon = home
    pos = wave(lambda a: f"{cx + r * math.cos(math.radians(lat)) * math.sin(a):.1f} {cy - r * math.sin(math.radians(lat)):.1f}")
    seen = wave(lambda a: "1" if math.cos(a) > 0.1 else "0")
    p.append(f'<g><animateTransform attributeName="transform" type="translate" values="{pos}" {spin(lon)}/>'
             f'<animate attributeName="opacity" values="{seen}" {spin(lon)}/>'
             f'<circle r="4" fill="none" stroke="{pin}" stroke-width="1.5"><animate attributeName="r" values="4;14" dur="1.6s" repeatCount="indefinite"/>'
             f'<animate attributeName="opacity" values="1;0" dur="1.6s" repeatCount="indefinite"/></circle><circle r="3.8" fill="{pin}"/></g>')
    return "".join(p)


def roller(words, ink, y=108, step=2.2):
    """Slot-machine words: each slides up into the slot, holds, and leaves as the next one arrives."""
    dur = len(words) * step
    keys = ";".join(f"{v:.4f}" for v in (0, 0.45 / dur, step / dur, (step + 0.45) / dur, 1))
    p, dots = [], []
    for i, w in enumerate(words):
        b = f'dur="{dur:.1f}s" begin="-{(dur - i * step) % dur:.2f}s" repeatCount="indefinite"'
        p.append(t(22, y, e(w) + f'<animateTransform attributeName="transform" type="translate" values="0 70;0 0;0 0;0 -70;0 -70" '
                   f'keyTimes="{keys}" calcMode="spline" keySplines=".2 .8 .2 1;0 0 1 1;.6 0 .4 1;0 0 1 1" {b}/>',
                   SERIF, 44, ink, ' font-style="italic" transform="translate(0 70)"'))
        dots.append(f'<circle cx="{25 + i * 12}" cy="186" r="3" fill="{ink}"><animate attributeName="opacity" values="1;.3" '
                    f'keyTimes="0;{step / dur:.4f}" calcMode="discrete" {b}/></circle>')
    return f'<g clip-path="url(#slot)">{"".join(p)}</g>{"".join(dots)}'


def marquee(text, seg, y, family, size, ink, dur, reverse=False, extra=""):
    """Endless ticker: three copies forced to one width each, slid by exactly one copy."""
    move = f"-{seg} 0;0 0" if reverse else f"0 0;-{seg} 0"
    copies = "".join(t(i * seg, y, e(text), family, size, ink, f' textLength="{seg}" lengthAdjust="spacing"{extra}') for i in range(3))
    return f'<g><animateTransform attributeName="transform" type="translate" values="{move}" dur="{dur}s" repeatCount="indefinite"/>{copies}</g>'


def tile(i, name, label, bg, ink, body, alt):
    """One of three 1/3-width cards; svg i is offset 4*i so the row's outer edges line up with the full-width cards."""
    cw, at = TILE_W, 3.1 + i * 0.15
    svg(name, 880 / 3, 222, alt,
        f'<defs><clipPath id="card"><rect width="{cw:.3f}" height="210" rx="14"/></clipPath>'
        f'<clipPath id="slot"><rect y="62" width="{cw:.3f}" height="62"/></clipPath>'
        '<linearGradient id="gl" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        '<stop offset=".5" stop-color="#fff" stop-opacity=".35"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>'
        f'<g transform="translate({4 * i} 0)"><g{delay(at, "ti")}><g clip-path="url(#card)">'
        f'<rect width="{cw:.3f}" height="210" fill="{bg}"/>'
        f'<rect{delay(at + 1.4, "sh")} y="-20" width="90" height="250" fill="url(#gl)" transform="translate(-260 0)"/>'
        f'<g{delay(at + 0.45, "f")}>{body}</g></g>'
        + t(24, 38, label, MONO, 12, ink, delay(at + 0.35, "f") + ' letter-spacing="1.2"')
        + f'<g{delay(at + 0.5, "f")}>' + t(cw - 35, 38, "&#8594;", MONO, 14, ink, delay(at + 1.3, "n")) + "</g></g></g>")


LINKS = [  # (card file, label, caption); the hrefs live in README.md
    ("site", "Website", SITE), ("linkedin", "LinkedIn", "in/albertirgi"), ("resume", "Résumé", "google docs"),
    ("email", "Email", "irgialbert@gmail.com"),
]


def links(at=4.2):
    """Footer row: one small card per link, because an SVG in <img> can't carry its own hrefs.
    Same 12px gaps and flush outer edges as tile()."""
    n = len(LINKS)
    cw = (880 - 12 * (n - 1)) / n
    for i, (name, label, cap) in enumerate(LINKS):
        a, accent = at + i * 0.12, [BLUE, RED, YELLOW][i % 3]
        svg(f"link-{name}", 880 / n, 112, f"{label}: {cap}",
            f'<defs><clipPath id="card"><rect width="{cw:.3f}" height="100" rx="14"/></clipPath></defs>'
            f'<g transform="translate({12 * i / n:g} 0)"><g{delay(a, "ti")}><g clip-path="url(#card)">'
            f'<rect width="{cw:.3f}" height="100" fill="{CREAM}"/>'
            f'<rect{delay(a + 0.6, "gx")} y="96" width="{cw:.3f}" height="4" fill="{accent}"/></g>'
            f'<g{delay(a + 0.35, "f")}><rect x="18" y="19" width="8" height="8" rx="2" fill="{accent}"/>'
            + t(34, 27, f"{i + 1:02d}", MONO, 11, MUTED, ' letter-spacing="1"')
            + t(cw - 30, 28, "&#8599;", MONO, 14, INK, ' class="nu"')
            + t(17, 68, e(label), SERIF, 34, INK, ' font-style="italic"')
            + t(18, 86, e(cap), MONO, 10, MUTED) + "</g></g></g>")


def replica(stars, at=3.6):
    """Featured-repo card. Left: what it is, the four scoring axes filling to PASS, the install command typing
    itself. Right: a night sky with one star per stargazer, lit as the counter climbs, and a constellation
    drawing itself between the brightest."""
    H, (x0, y0, w, h) = 350, (536, 22, 322, 306)
    n, rng = min(stars, 300), random.Random(29)
    pts = []
    while len(pts) < n:
        x, y = rng.uniform(x0 + 10, x0 + w - 10), rng.uniform(y0 + 10, y0 + h - 10)
        if not (x < x0 + 236 and y > y0 + h - 104):  # keep the corner under the counter clear
            pts.append((x, y, rng.random() ** 2.5))  # brightness: many faint, a few bright
    sky = []
    for k, (x, y, b) in enumerate(pts):
        t0, lit = at + 0.5 + 0.84 * k / n, 0.45 + 0.55 * b  # lit in step with the counter
        sky.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{0.6 + 1.9 * b:.2f}" fill="{rng.choice(["#fff", "#fff", "#ffe9a8", "#c8d3ff"])}" '
                   f'opacity="0"><set attributeName="opacity" to="{lit:.2f}" begin="{t0:.2f}s"/><animate attributeName="opacity" '
                   f'values="{lit:.2f};{0.1 + 0.3 * b:.2f};{lit:.2f}" dur="{rng.uniform(1.5, 4):.1f}s" begin="{t0 + 0.3:.2f}s" repeatCount="indefinite"/></circle>')
    bright = sorted(pts, key=lambda q: -q[2])[:7]
    chain = [min(bright)]
    while len(chain) < len(bright):
        chain.append(min((q for q in bright if q not in chain), key=lambda q: math.dist(q[:2], chain[-1][:2])))
    lines = (f'<polyline points="{" ".join(f"{x:.1f},{y:.1f}" for x, y, _ in chain)}" fill="none" stroke="#c8d3ff" stroke-opacity=".5" '
             'stroke-width=".9" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1"><animate attributeName="stroke-dashoffset" '
             f'values="1;0" keyTimes="0;1" calcMode="spline" keySplines=".4 0 .2 1" dur="2.4s" begin="{at + 1.6:.2f}s" fill="freeze"/></polyline>')
    glints = "".join(
        f'<path d="M{x:.1f} {y - 8:.1f}V{y + 8:.1f}M{x - 8:.1f} {y:.1f}H{x + 8:.1f}" stroke="#fff" stroke-width=".8" stroke-linecap="round" opacity="0">'
        f'<animate attributeName="opacity" values="0;.9;0" dur="{rng.uniform(2.5, 4.5):.1f}s" begin="{at + 1.6 + rng.uniform(0, 2):.2f}s" '
        'repeatCount="indefinite"/></path>' for x, y, _ in bright[:4])
    shoot = (f'<line x1="0" y1="0" x2="80" y2="-30" stroke="url(#trail)" stroke-width="1.6" stroke-linecap="round" opacity="0">'
             f'<animateTransform attributeName="transform" type="translate" values="{x0 + w + 40} {y0 + 30};{x0 + 80} {y0 + 200};{x0 + 80} {y0 + 200}" '
             f'keyTimes="0;.12;1" dur="6s" begin="{at + 3:.2f}s" repeatCount="indefinite"/><animate attributeName="opacity" values="0;1;0;0" '
             f'keyTimes="0;.04;.12;1" dur="6s" begin="{at + 3:.2f}s" repeatCount="indefinite"/></line>')
    axes = "".join(
        t(44 + j * 92, 272, name, MONO, 10, MUTED, ' letter-spacing="1"')
        + f'<rect x="{44 + j * 92}" y="280" width="78" height="4" rx="2" fill="{RULE}"/>'
        + f'<rect{delay(at + 0.9 + j * 0.25, "gx")} x="{44 + j * 92}" y="280" width="78" height="4" rx="2" fill="{BLUE}"/>'
        for j, name in enumerate(["LAYOUT", "STYLE", "PIXELS", "MOTION"]))
    step = 8.4  # Geist Mono advance at 14px
    typed = f'dur="{len(INSTALL) * 0.05:.2f}s" begin="{at + 1.2:.2f}s" calcMode="discrete" fill="freeze"'
    body = (
        f'<defs><clipPath id="card"><rect width="880" height="{H}" rx="14"/></clipPath>'
        f'<clipPath id="sky"><rect x="{x0}" y="{y0}" width="{w}" height="{h}" rx="12"/></clipPath>'
        f'<clipPath id="type"><rect x="62" y="306" height="24" width="0"><animate attributeName="width" '
        f'values="{";".join(f"{k * step:.1f}" for k in range(len(INSTALL) + 1))}" {typed}/></rect></clipPath>'
        '<linearGradient id="night" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#070a1c"/><stop offset="1" stop-color="#1c2156"/></linearGradient>'
        '<radialGradient id="dusk" cx=".7" cy="1.05" r=".75"><stop offset="0" stop-color="#2f55ff" stop-opacity=".45"/><stop offset="1" stop-color="#2f55ff" stop-opacity="0"/></radialGradient>'
        '<linearGradient id="trail" x1="0" x2="1"><stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
        f'<linearGradient id="shim" gradientUnits="userSpaceOnUse" x1="{x0}" y1="0" x2="{x0 + 260}" y2="0">'
        f'<stop offset="0" stop-color="{CREAM}"/><stop offset=".4" stop-color="{CREAM}"/><stop offset=".5" stop-color="#ffd34d"/>'
        f'<stop offset=".6" stop-color="{CREAM}"/><stop offset="1" stop-color="{CREAM}"/>'
        '<animateTransform attributeName="gradientTransform" type="translate" values="-300 0;300 0;300 0" keyTimes="0;.4;1" '
        f'dur="5s" begin="{at + 2:.2f}s" repeatCount="indefinite"/></linearGradient></defs>'
        f'<g clip-path="url(#card)"><rect width="880" height="{H}" fill="{CREAM}"/>'
        f'<g{delay(at, "f")}><rect class="live" x="44" y="49" width="8" height="8" rx="2" fill="{BLUE}"/>'
        + t(62, 57, "FEATURED  ·  AN AGENT SKILL FOR CODING AGENTS", MONO, 12, MUTED, ' letter-spacing="1"') + "</g>"
        + t(38, 166, f'{e(FEATURED)}<tspan font-style="normal" fill="{BLUE}">.</tspan>', SERIF, 120, INK,
            delay(at + 0.15, "r") + ' font-style="italic" letter-spacing="-2.5"')
        + f'<g{delay(at + 0.35, "r")}>' + t(44, 210, "Rebuild any UI from a reference,", SANS, 18, BODY)
        + t(44, 236, "and prove it with a score.", SANS, 18, BODY) + "</g>"
        + f'<g{delay(at + 0.6, "f")}>{axes}</g>'
        + f'<g{delay(at + 2, "p")}><rect x="412" y="266" width="56" height="22" rx="11" fill="{INK}"/>'
        + t(440, 281, "PASS", MONO, 11, CREAM, ' text-anchor="middle" letter-spacing="1"') + "</g>"
        + f'<g{delay(at + 1.1, "f")}>' + t(44, 322, "$", MONO, 14, BLUE)
        + f'<g clip-path="url(#type)">{t(62, 322, e(INSTALL), MONO, 14, INK)}</g>'
        + f'<rect x="62" y="309" width="8" height="16" fill="{BLUE}"><animate attributeName="x" '
        + f'values="{";".join(f"{62 + k * step:.1f}" for k in range(len(INSTALL) + 1))}" {typed}/>'
        + '<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.51;1" dur="1s" repeatCount="indefinite"/></rect></g>'
        + f'<g{delay(at - 0.2, "f")} clip-path="url(#sky)"><rect x="{x0}" y="{y0}" width="{w}" height="{h}" fill="url(#night)"/>'
        + f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" fill="url(#dusk)"/>'
        + '<g><animateTransform attributeName="transform" type="translate" values="0 0;-7 3;0 0" dur="24s" repeatCount="indefinite"/>'
        + lines + "".join(sky) + glints + "</g>" + shoot
        + count(stars, "stars", at + 0.5, x0 + 24, y0 + h - 44, 60, "url(#shim)")
        + t(x0 + 26, y0 + h - 20, "ONE FOR EVERY STARGAZER", MONO, 10, "#9aa3c7", ' letter-spacing="1"') + "</g></g>"
    )
    svg(FEATURED, 880, H + 12, f"{FEATURED}: rebuild any UI from a reference and prove it with a score. {stars} stars on GitHub.", body)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    days = fetch_days()
    repos = [r for r in json.loads(get(f"https://api.github.com/users/{USER}/repos?per_page=100")) if not r["fork"]]
    stars = next(r["stargazers_count"] for r in repos if r["name"] == FEATURED)
    with open(os.path.join(OUT, "portrait.txt")) as f:
        hero(f.read().splitlines())
    heatmap(days)
    activity(days)
    white = "#ffffff"
    tile(0, "globe", "BASED IN", BLUE, white,
         t(22, 100, "Bali", SERIF, 46, white) + t(24, 126, "INDONESIA", MONO, 11, white, ' letter-spacing="1" opacity=".8"')
         + t(24, 144, "GMT+8", MONO, 11, white, ' letter-spacing="1" opacity=".8"') + globe(land_dots(), white, YELLOW, TILE_W - 82, 128),
         "BASED IN: Bali, Indonesia (GMT+8), pinned on a spinning dotted globe")
    tile(1, "build", "I BUILD", RED, white, roller(BUILD, white) + t(24, 150, "Software Engineer at 3C Solutions.", SANS, 13, white),
         f"I BUILD: {', '.join(BUILD)}. Software Engineer at 3C Solutions.")
    tile(2, "hire", "HIRE ME", YELLOW, INK,
         '<defs><linearGradient id="edge" x1="0" x2="1"><stop offset="0" stop-color="#000"/><stop offset=".12" stop-color="#fff"/>'
         f'<stop offset=".88" stop-color="#fff"/><stop offset="1" stop-color="#000"/></linearGradient><mask id="fade"><rect width="{TILE_W:.3f}" '
         'height="210" fill="url(#edge)"/></mask></defs><g mask="url(#fade)">'
         + marquee("Open to work —\u00a0", 300, 106, SERIF, 50, INK, 8, extra=' font-style="italic"')
         + marquee("ON-SITE · HYBRID · REMOTE ·\u00a0", 236, 146, MONO, 12, INK, 6, reverse=True, extra=' letter-spacing="1.5"') + "</g>"
         + t(24, 188, "irgialbert@gmail.com", MONO, 12, INK) + t(24 + 20 * 7.2 + 8, 188, "&#8599;", MONO, 12, INK, ' class="nu"'),
         "HIRE ME: open to work, on-site, hybrid or remote. irgialbert@gmail.com")
    for theme, fill in [("dark", "#e6edf3"), ("light", "#1f2328")]:
        svg(f"title-{theme}", 880, 64, "What I've built",
            t(2, 46, big("What I've", "built"), SERIF, 34, fill, delay(3.5, "r")))
    replica(stars)
    links()
    print(f"wrote {OUT}: {sum(d['count'] for d in days):,} contributions, {stars} stars on {FEATURED}")
