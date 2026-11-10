#!/usr/bin/env python3
"""
Frame replica's demo GIF as a profile card: cream bezel, rounded screen, rounded card corners and the
12px gap below baked in like the SVG cards. A GIF with transparency triples in size, so the corners are
matted to the page colour instead, one GIF per GitHub theme (cards/replica-demo-{dark,light}.gif, picked
by <picture> in the README). GitHub plays GIFs in <img>; a GIF inside an SVG card isn't reliable.
Needs Pillow and ffmpeg; run by hand when the demo changes:
  python3 scripts/demo.py
"""
import os
import subprocess
import tempfile
import urllib.request

from PIL import Image, ImageDraw

SRC = "https://github.com/albertirgi/replica/raw/main/.github/assets/demo-family.gif"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cards", "replica-demo-{}.gif")
W, PAD, GAP, R, SR = 880, 20, 12, 14, 10  # card width, bezel, gap below, card radius, screen radius
CREAM = (243, 243, 241)
PAGE = {"dark": (13, 17, 23), "light": (255, 255, 255)}  # github's canvas colours


def rounded(size, radius, box, ss=4):
    """Anti-aliased rounded-rect mask, drawn at ss x and scaled down."""
    m = Image.new("L", (size[0] * ss, size[1] * ss), 0)
    ImageDraw.Draw(m).rounded_rectangle([v * ss for v in box], radius=radius * ss, fill=255)
    return m.resize(size, Image.LANCZOS)


with tempfile.TemporaryDirectory() as tmp:
    src = os.path.join(tmp, "demo.gif")
    urllib.request.urlretrieve(SRC, src)
    sw, (w0, h0) = W - 2 * PAD, Image.open(src).size
    sh = round(h0 * sw / w0 / 2) * 2
    H = sh + 2 * PAD + GAP
    card, screen = rounded((W, H), R, (0, 0, W, H - GAP)), rounded((W, H), SR, (PAD, PAD, PAD + sw, PAD + sh))
    for theme, page in PAGE.items():
        bezel = Image.composite(Image.new("RGB", (W, H), CREAM), Image.new("RGB", (W, H), page), card).convert("RGBA")
        bezel.putalpha(screen.point(lambda v: 255 - v))  # see-through where the screen goes
        bezel.save(os.path.join(tmp, "bezel.png"))
        out = OUT.format(theme)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-i", os.path.join(tmp, "bezel.png"), "-filter_complex",
                        f"[0:v]scale={sw}:{sh}:flags=lanczos,pad={W}:{H}:{PAD}:{PAD}[v];[v][1:v]overlay=0:0,split[a][b];"
                        "[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=none:diff_mode=rectangle",
                        "-loop", "0", out], check=True)
        print(f"wrote {out}: {W}x{H}, {os.path.getsize(out) / 1e6:.1f} MB")
