#!/usr/bin/env python3
"""
Turn a photo into a monochrome ASCII-art SVG that "types" itself in row by row
(SMIL clip wipes, which GitHub plays inside <img>), then freezes.
The subject is cut out with rembg (isnet-anime model) and put on white, so the
background prints blank and dark lines/hair print dense, like ink on paper.
Run locally when the photo changes (defaults to the GitHub avatar):
  uv run --python 3.12 --with "rembg[cpu]" --with pillow python scripts/portrait.py [photo]
"""
import html
import io
import os
import sys
import urllib.request

from PIL import Image, ImageFilter, ImageOps
from rembg import new_session, remove

SRC = sys.argv[1] if len(sys.argv) > 1 else "https://github.com/albertirgi.png?size=460"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ascii-portrait.svg")
NAME = "Albert Muhammad Irgi"

COLS = int(os.environ.get("COLS", 150))
ART_W = 800
CELL_W = ART_W / COLS
CELL_H = CELL_W * 15 / 8  # ~monospace glyph aspect
RAMP = " .`:-=+*cs#%@"    # bright (blank) -> dark (dense)
GAMMA = float(os.environ.get("GAMMA", 0.25))  # <1 lightens mids -> sparser chars
WHITE_FLOOR = 0.93        # luminance above this prints nothing (the white background)
ALPHA_CUT = 80            # rembg alpha below this is background (drops faint ghosts, keeps soft hair)
LINE_THICKEN = int(os.environ.get("THICKEN", 5))  # MinFilter size: fattens dark line art so it survives downsampling
CROP = tuple(float(v) for v in os.environ.get("CROP", "0.13,0.02,0.87,0.76").split(","))  # square box, fractions of w/h

PAD, TITLE_H, STATUS_H = 20, 30, 30
BG, BG2, FRAME, MUTED, INK = "#0d1117", "#111722", "#30363d", "#7d8590", "#c9d1d9"
ROW_DUR = 5.8 / COLS * 15 / 8  # whole portrait prints in ~6s

raw = urllib.request.urlopen(SRC).read() if SRC.startswith("http") else open(SRC, "rb").read()
cut = remove(Image.open(io.BytesIO(raw)).convert("RGB"), session=new_session("isnet-anime"))
cut.putalpha(cut.getchannel("A").point(lambda a: 255 if a >= ALPHA_CUT else 0))
im = Image.new("RGBA", cut.size, "white")
im.alpha_composite(cut)
im = im.convert("L").filter(ImageFilter.MinFilter(LINE_THICKEN))
im = ImageOps.autocontrast(im.crop([round(c * im.size[i % 2]) for i, c in enumerate(CROP)]), cutoff=1)
w, h = im.size
rows_n = round(COLS * h / w * 8 / 15)
im = im.resize((COLS, rows_n), Image.LANCZOS)
px = im.load()

rows = []
for y in range(rows_n):
    line = ""
    for x in range(COLS):
        lum = (px[x, y] / 255) ** GAMMA
        line += " " if lum > WHITE_FLOOR else RAMP[round((1 - lum) * (len(RAMP) - 1))]
    rows.append(line)

art_h = rows_n * CELL_H
cw, ch = ART_W + PAD * 2, TITLE_H + art_h + STATUS_H + PAD
top = TITLE_H + PAD * 0.35
p = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{cw}" height="{ch:.0f}" viewBox="0 0 {cw} {ch:.0f}" '
    'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
    f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BG2}"/>'
    f'<stop offset="1" stop-color="{BG}"/></linearGradient></defs>',
    f'<rect width="{cw}" height="{ch:.0f}" rx="12" fill="url(#bg)"/>',
    f'<rect x="0.5" y="0.5" width="{cw-1}" height="{ch-1:.0f}" rx="12" fill="none" stroke="{FRAME}"/>',
    f'<line x1="0" y1="{TITLE_H}" x2="{cw}" y2="{TITLE_H}" stroke="{FRAME}"/>',
]
for i, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
    p.append(f'<circle cx="{PAD + i*16}" cy="{TITLE_H/2}" r="5" fill="{c}"/>')
p.append(f'<text x="{cw/2}" y="{TITLE_H/2 + 4}" fill="{MUTED}" font-size="12" text-anchor="middle">'
         'albertirgi@github: ~$ ./portrait.sh</text>')

for ry, line in enumerate(rows):
    if not line.strip():
        continue
    row_y, t = top + ry * CELL_H, ry * ROW_DUR
    p.append(f'<clipPath id="r{ry}"><rect x="{PAD}" y="{row_y:.1f}" height="{CELL_H:.2f}" width="0">'
             f'<animate attributeName="width" to="{ART_W}" begin="{t:.3f}s" dur="{ROW_DUR:.2f}s" fill="freeze"/>'
             f'</rect></clipPath>')
    p.append(f'<g clip-path="url(#r{ry})"><text xml:space="preserve" x="{PAD}" y="{row_y + CELL_H*0.74:.1f}" '
             f'fill="{INK}" font-size="{CELL_H*0.86:.1f}" textLength="{ART_W}" lengthAdjust="spacing">'
             f'{html.escape(line)}</text></g>')
    p.append(f'<rect y="{row_y+1:.1f}" width="{CELL_W:.2f}" height="{CELL_H-2:.2f}" fill="{INK}" opacity="0">'
             f'<animate attributeName="x" from="{PAD}" to="{PAD+ART_W}" begin="{t:.3f}s" dur="{ROW_DUR:.2f}s" fill="freeze"/>'
             f'<set attributeName="opacity" to="0.85" begin="{t:.3f}s"/>'
             f'<set attributeName="opacity" to="0" begin="{t+ROW_DUR:.3f}s"/></rect>')

sy = TITLE_H + art_h + PAD * 0.35
p.append(f'<line x1="0" y1="{sy:.1f}" x2="{cw}" y2="{sy:.1f}" stroke="{FRAME}"/>')
prompt = f"albertirgi@github:~$ whoami {NAME} "
p.append(f'<text x="{PAD}" y="{sy+19:.1f}" fill="{MUTED}" font-size="13">'
         f'albertirgi@github:~$ whoami <tspan fill="{INK}">{NAME}</tspan></text>')
p.append(f'<rect x="{PAD + len(prompt)*13*0.6:.1f}" y="{sy+7:.1f}" width="8" height="14" fill="{INK}">'
         '<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" dur="1s" repeatCount="indefinite"/></rect>')
p.append("</svg>")

with open(OUT, "w") as f:
    f.write("".join(p))
print(f"wrote {OUT}: {cw}x{ch:.0f}, {COLS}x{rows_n} chars")
