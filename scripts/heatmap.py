#!/usr/bin/env python3
"""
Scrape the public contributions calendar (no token) and render it as an
animated, terminal-styled heatmap SVG. Stdlib only, so CI needs no pip install.
Run daily by .github/workflows/update-heatmap.yml.
"""
import datetime
import os
import re
import sys
import urllib.request

USER = os.environ.get("GH_PROFILE_USER", "albertirgi")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "contrib-heatmap.svg")

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]  # github data-level 0..4
CELL, GAP = 12, 3
STEP = CELL + GAP
PAD, LEFT_W, TOP_H, TITLE_H, STATS_H = 22, 30, 20, 30, 88
BG, BG2, FRAME = "#0a0e14", "#0d1420", "#1f6feb"
MUTED, ACCENT, GREEN, GOLD = "#7d8590", "#22d3ee", "#39d353", "#f2cc60"
COL_T, ROW_T, CELL_DUR = 0.018, 0.045, 0.42  # diagonal reveal timing


def fetch_days():
    req = urllib.request.Request(f"https://github.com/users/{USER}/contributions",
                                 headers={"User-Agent": "profile-readme-bot/1.0"})
    page = urllib.request.urlopen(req, timeout=30).read().decode()
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


def streaks(days):
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] else 0
        longest = max(longest, run)
    i = len(days) - 1
    if days[i]["count"] == 0:
        i -= 1  # today isn't over yet -- don't break the streak on it
    current = 0
    while i >= 0 and days[i]["count"]:
        current, i = current + 1, i - 1
    return current, longest


def render(days):
    first = datetime.date.fromisoformat(days[0]["date"])
    cols = [[None] * ((first.weekday() + 1) % 7)]  # sunday = row 0
    for d in days:
        if len(cols[-1]) == 7:
            cols.append([])
        cols[-1].append(d)

    w = PAD + LEFT_W + len(cols) * STEP + PAD
    h = TITLE_H + TOP_H + 7 * STEP + STATS_H + PAD
    gx0, gy0 = PAD + LEFT_W, TITLE_H + TOP_H
    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        "<style>@keyframes cell{0%{opacity:0;transform:translateY(-6px)}100%{opacity:1;transform:translateY(0)}}"
        f".c{{opacity:0;animation:cell {CELL_DUR}s cubic-bezier(.2,.8,.2,1) both}}</style>",
        f'<defs><linearGradient id="hbg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BG2}"/>'
        f'<stop offset="1" stop-color="{BG}"/></linearGradient></defs>',
        f'<rect width="{w}" height="{h}" rx="12" fill="url(#hbg)"/>',
        f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="12" fill="none" stroke="{FRAME}" stroke-opacity="0.55"/>',
        f'<line x1="0" y1="{TITLE_H}" x2="{w}" y2="{TITLE_H}" stroke="{FRAME}" stroke-opacity="0.35"/>',
    ]
    for i, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        p.append(f'<circle cx="{PAD + i*16}" cy="{TITLE_H/2}" r="5" fill="{c}"/>')
    p.append(f'<text x="{w/2}" y="{TITLE_H/2 + 4}" fill="{MUTED}" font-size="12" text-anchor="middle">'
             f'albertirgi@github: ~/contributions --graph</text>')

    prev = None
    for ci, col in enumerate(cols):
        date = datetime.date.fromisoformat(next(c for c in col if c)["date"])
        if date.month != prev and (prev or date.day <= 7):  # skip a partial first month
            p.append(f'<text x="{gx0 + ci*STEP}" y="{TITLE_H + 14}" fill="{MUTED}" font-size="10">{date:%b}</text>')
        prev = date.month
    for ri, name in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        p.append(f'<text x="{PAD}" y="{gy0 + ri*STEP + CELL*0.78:.1f}" fill="{MUTED}" font-size="9">{name}</text>')

    for ci, col in enumerate(cols):
        for ri, d in enumerate(col):
            if d:
                s = "" if d["count"] == 1 else "s"
                p.append(f'<rect class="c" x="{gx0 + ci*STEP}" y="{gy0 + ri*STEP}" width="{CELL}" height="{CELL}" '
                         f'rx="2.5" fill="{PALETTE[d["level"]]}" style="animation-delay:{ci*COL_T + ri*ROW_T:.3f}s">'
                         f'<title>{d["date"]}: {d["count"]} contribution{s}</title></rect>')

    ly = gy0 + 7 * STEP + 6
    lx = w - PAD - (len(PALETTE) * CELL + 34)
    p.append(f'<text x="{lx - 6}" y="{ly + CELL*0.8:.1f}" fill="{MUTED}" font-size="10" text-anchor="end">Less</text>')
    for i, c in enumerate(PALETTE):
        p.append(f'<rect x="{lx + i*CELL}" y="{ly}" width="{CELL-1}" height="{CELL-1}" rx="2.2" fill="{c}"/>')
    p.append(f'<text x="{lx + len(PALETTE)*CELL + 4}" y="{ly + CELL*0.8:.1f}" fill="{MUTED}" font-size="10">More</text>')

    sep = ly + CELL + 14
    p.append(f'<line x1="0" y1="{sep}" x2="{w}" y2="{sep}" stroke="{FRAME}" stroke-opacity="0.25"/>')
    total = sum(d["count"] for d in days)
    best = max(days, key=lambda d: d["count"])
    cur, longest = streaks(days)
    y = sep + 24
    p.append(f'<text x="{PAD}" y="{y}" font-size="13" fill="{GREEN}"><tspan font-weight="700">{total:,}</tspan>'
             f'<tspan fill="{MUTED}"> contributions in the last year</tspan></text>')
    p.append(f'<text x="{w - PAD}" y="{y}" font-size="12" fill="{MUTED}" text-anchor="end">'
             f'{days[0]["date"]} &#8594; {days[-1]["date"]}</text>')
    y += 24
    p.append(f'<text x="{PAD}" y="{y}" font-size="13" fill="{MUTED}">current streak '
             f'<tspan fill="{ACCENT}" font-weight="700">{cur} days</tspan>   &#183;   longest '
             f'<tspan fill="{ACCENT}" font-weight="700">{longest} days</tspan></text>')
    p.append(f'<text x="{w - PAD}" y="{y}" font-size="12" fill="{MUTED}" text-anchor="end">best day '
             f'<tspan fill="{GOLD}" font-weight="700">{best["count"]}</tspan> on {best["date"]}</text>')
    p.append("</svg>")
    return "".join(p)


if __name__ == "__main__":
    days = fetch_days()
    assert streaks([{"count": c} for c in (1, 1, 0, 1, 1, 1, 0)]) == (3, 3)  # trailing 0 = today, ignored
    svg = render(days)
    with open(OUT, "w") as f:
        f.write(svg)
    print(f"wrote {OUT}: {len(days)} days, {sum(d['count'] for d in days)} contributions")
