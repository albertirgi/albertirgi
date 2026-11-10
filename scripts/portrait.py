#!/usr/bin/env python3
"""
Turn a photo into ASCII-art rows (cards/portrait.txt) that scripts/cards.py prints into the hero card.
Positive print, like the photo itself: dark areas print dense, light ones sparse, inside a soft circle
so the dark backdrop frames the lit subject. Pillow only:
  python3 scripts/portrait.py [photo]        (defaults to the GitHub avatar)
Knobs: COLS (detail), GAMMA (>1 pushes mid-tones toward blank), CROP (fractions of w/h).
"""
import io
import os
import sys
import urllib.request

from PIL import Image, ImageDraw, ImageFilter, ImageOps

SRC = sys.argv[1] if len(sys.argv) > 1 else "https://github.com/albertirgi.png?size=460"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cards", "portrait.txt")
COLS = int(os.environ.get("COLS", 180))
GAMMA = float(os.environ.get("GAMMA", 1.7))
CROP = tuple(float(v) for v in os.environ.get("CROP", "0,0,1,1").split(","))
RAMP = " .:-=+*#%@"  # sparse -> dense
FEATHER = 20  # px of soft edge on the circle (source pixels)

raw = urllib.request.urlopen(SRC).read() if SRC.startswith("http") else open(SRC, "rb").read()
im = Image.open(io.BytesIO(raw)).convert("L")
im = ImageOps.autocontrast(im.crop([round(c * im.size[i % 2]) for i, c in enumerate(CROP)]), cutoff=1)
ink = ImageOps.invert(im).point(lambda v: round(255 * (v / 255) ** GAMMA))
frame = Image.new("L", im.size, 0)
ImageDraw.Draw(frame).ellipse((FEATHER, FEATHER, im.size[0] - FEATHER, im.size[1] - FEATHER), fill=255)
ink = Image.composite(ink, Image.new("L", im.size, 0), frame.filter(ImageFilter.GaussianBlur(FEATHER / 2)))

rows_n = round(COLS * im.size[1] / im.size[0] * 8 / 15)  # glyphs are ~8:15
px = ink.resize((COLS, rows_n), Image.LANCZOS).load()
rows = ["".join(" " if px[x, y] < 10 else RAMP[max(1, round(px[x, y] / 255 * (len(RAMP) - 1)))] for x in range(COLS))
        for y in range(rows_n)]

with open(OUT, "w") as f:
    f.write("\n".join(rows) + "\n")
print(f"wrote {OUT}: {COLS}x{rows_n} chars")
