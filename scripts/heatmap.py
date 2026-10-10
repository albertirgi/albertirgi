#!/usr/bin/env python3
"""
Scrape the public contributions calendar (no token) and render it as an
animated, frameless heatmap SVG (transparent bg, light/dark aware). Stdlib only, so CI needs no pip install.
Run daily by .github/workflows/update-heatmap.yml.
"""
import datetime
import os
import re
import sys
import urllib.request

USER = os.environ.get("GH_PROFILE_USER", "albertirgi")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "contrib-heatmap.svg")

DARK = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]   # github data-level 0..4
LIGHT = ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]  # transparent bg -> follow the viewer's theme
CELL, STEP, LEFT_W, TOP_H = 13, 16, 34, 24
COL_T, ROW_T = 0.065, 0.036  # diagonal pop-in timing (~3.6s total)
CSS = (
    ".lbl{fill:#7d8590;font-size:13px;font-weight:600}.total{fill:#e6edf3;font-size:15px;font-weight:700}"
    ".c{transform-box:fill-box;transform-origin:center;opacity:0;animation:pop .55s ease-out both}"
    ".g{animation:pop .55s ease-out both,flash .7s ease-out both}"
    "@keyframes pop{0%{opacity:0;transform:scale(.2)}60%{opacity:1;transform:scale(1.1)}100%{opacity:1;transform:scale(1)}}"
    "@keyframes flash{0%,45%{filter:brightness(2.4)}100%{filter:brightness(1)}}"
    + "".join(f".l{i}{{fill:{c}}}" for i, c in enumerate(DARK))
    + "@media (prefers-color-scheme:light){.total{fill:#1f2328}"
    + "".join(f".l{i}{{fill:{c}}}" for i, c in enumerate(LIGHT)) + "}"
    "@media (prefers-reduced-motion:reduce){.c{opacity:1!important;animation:none!important}}"
)


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


def render(days):
    first = datetime.date.fromisoformat(days[0]["date"])
    cols = [[None] * ((first.weekday() + 1) % 7)]  # sunday = row 0
    for d in days:
        if len(cols[-1]) == 7:
            cols.append([])
        cols[-1].append(d)

    w, h = LEFT_W + len(cols) * STEP + 6, TOP_H + 7 * STEP + 22
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
         'font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif">', f"<style>{CSS}</style>"]

    prev = None
    for ci, col in enumerate(cols):
        date = datetime.date.fromisoformat(next(c for c in col if c)["date"])
        if date.month != prev and (prev or date.day <= 7):  # skip a partial first month
            p.append(f'<text class="lbl" x="{LEFT_W + ci*STEP}" y="16">{date:%b}</text>')
        prev = date.month
    for ri, name in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        p.append(f'<text class="lbl" x="2" y="{TOP_H + ri*STEP + 11}">{name}</text>')

    for ci, col in enumerate(cols):
        for ri, d in enumerate(col):
            if d:
                s = "" if d["count"] == 1 else "s"
                cls = f'c g l{d["level"]}' if d["count"] else "c l0"
                p.append(f'<rect class="{cls}" x="{LEFT_W + ci*STEP}" y="{TOP_H + ri*STEP}" width="{CELL}" '
                         f'height="{CELL}" rx="2.5" style="animation-delay:{ci*COL_T + ri*ROW_T:.3f}s">'
                         f'<title>{d["date"]}: {d["count"]} contribution{s}</title></rect>')

    total = sum(d["count"] for d in days)
    p.append(f'<text class="total" x="{LEFT_W}" y="{h - 6}">{total:,} contributions in the last year</text></svg>')
    return "".join(p)


if __name__ == "__main__":
    days = fetch_days()
    svg = render(days)
    with open(OUT, "w") as f:
        f.write(svg)
    print(f"wrote {OUT}: {len(days)} days, {sum(d['count'] for d in days)} contributions")
