"""Build logo 17: "ماستريكس" as vector outlines with the letter dots (إعجام) split out.

Amiri stores each dotted letter as a composite glyph: the skeleton is the first component
(the one carrying USE_MY_METRICS) and the dots are further components. Shaping with HarfBuzz and
walking the components gives a skeleton path and a dots path, even where a dot touches a letter.

Usage: python3 -I scripts/ijam_svg.py   ->  logos/assets/ijam.svg
"""
import io
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
FONT = ROOT / "node_modules/@fontsource/amiri/files/amiri-arabic-700-normal.woff2"
WORD = "ماستريكس"
USE_MY_METRICS = 0x0200

tt = TTFont(FONT)
tt.flavor = None
buf = io.BytesIO()
tt.save(buf)
font = hb.Font(hb.Face(buf.getvalue()))
glyf, order, gs = tt["glyf"], tt.getGlyphOrder(), tt.getGlyphSet()

b = hb.Buffer()
b.add_str(WORD)
b.guess_segment_properties()
hb.shape(font, b)

skel, dots = SVGPathPen(gs), SVGPathPen(gs)
bounds = BoundsPen(gs)
x, n_dots = 0, 0
for info, pos in zip(b.glyph_infos, b.glyph_positions):
    name = order[info.codepoint]
    ox, oy = x + pos.x_offset, pos.y_offset
    g = glyf[name]
    parts = []
    if g.isComposite():
        base = next((i for i, c in enumerate(g.components) if c.flags & USE_MY_METRICS), 0)
        for i, c in enumerate(g.components):
            a, bb, cc, d = (c.transform[0][0], c.transform[0][1], c.transform[1][0], c.transform[1][1]) if hasattr(c, "transform") else (1, 0, 0, 1)
            parts.append((c.glyphName, (a, bb, cc, d, ox + c.x, oy + c.y), i == base))
    else:
        parts.append((name, (1, 0, 0, 1, ox, oy), True))
    for comp, tr, is_skel in parts:
        gs[comp].draw(TransformPen(skel if is_skel else dots, tr))
        gs[comp].draw(TransformPen(bounds, tr))
        n_dots += 0 if is_skel else 1
    x += pos.x_advance

x0, y0, x1, y1 = bounds.bounds
pad = 40
vb = f"{x0 - pad:.0f} {-(y1 + pad):.0f} {x1 - x0 + 2 * pad:.0f} {y1 - y0 + 2 * pad:.0f}"
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}">
<g transform="scale(1 -1)"><path class="skel" d="{skel.getCommands()}"/><path class="dots" d="{dots.getCommands()}"/></g>
</svg>
'''
out = ROOT / "logos/assets/ijam.svg"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(svg)
print(out, "dot components:", n_dots, "viewBox", vb)
