#!/usr/bin/env python3
"""Cut the phone screens out of the App Store images, one set per page language.

    python3 tools/store-screens.py ../not-yet/build/store-final-1.1.1

Reads <dir>/<store locale>/iphone/01.png … 08.png (1320 × 2868, framed by the app repo's
docs/design/store-shots/render.html) and writes assets/img/<code>/<name>-<720|360>.webp.
The phone frame is found in the image; a screen cut off at the bottom of the store image
is filled up with its last colour (the site only ever shows the top or the bottom part).
The Dynamic Island drawn into the store image is painted out: the site draws one clean island
on every phone (home.css), and two islands on top of each other left a corner.
Needs Pillow.
"""
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
LOCALES = {'en': 'en-US', 'de': 'de-DE', 'es': 'es-ES', 'fr': 'fr-FR', 'it': 'it', 'pt': 'pt-BR', 'ja': 'ja', 'ko': 'ko'}
NAMES = ['home', 'lock', 'boss', 'alarm', 'week', 'focus', 'nights', 'piggy']  # store images 01–08
CQ = 13.2                 # 1 cqw of the 1320 px store image
SCR = 2868 / 1320         # screen aspect
W, H = 720, 1565          # site screens


def frame(p, ground):
    """A pixel of the dark phone frame (not the light or dark ground next to it)."""
    return sum(abs(a - b) for a, b in zip(p, ground)) > 90 and sum(p) < 200


def screen(path):
    im = Image.open(path).convert('RGB')
    y = int(im.height * .75)  # every phone covers this row
    left = next(x for x in range(im.width // 2) if frame(im.getpixel((x, y)), im.getpixel((4, y))))
    dw = 100 - 2 * left / CQ  # device width in cqw (render.html: --dw)
    r = dw * .156 * CQ        # outer corner radius
    top = y                   # walk up the left frame edge to where the corner starts
    while top > 0 and frame(im.getpixel((left + 3, top - 1)), im.getpixel((4, top - 1))):
        top -= 1
    top -= r - (r * r - (r - 3) ** 2) ** .5
    pad = dw * .024 * CQ
    x0, y0, sw = left + pad, top + pad, dw * .952 * CQ
    return im.crop((round(x0), round(y0), round(x0 + sw), round(min(y0 + sw * SCR, im.height))))


def erase_island(im):
    """Fill the island's box (720 px screen) column by column from the colours just above and below it."""
    px = im.load()
    for x in range(200, 513):
        a, b = px[x, 9], px[x, 89]
        for y in range(10, 89):
            t = (y - 9) / 80
            px[x, y] = tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def main(src):
    for code, loc in LOCALES.items():
        out = ROOT / 'assets' / 'img' / code
        out.mkdir(parents=True, exist_ok=True)
        for i, name in enumerate(NAMES, 1):
            s = screen(src / loc / 'iphone' / f'{i:02d}.png')
            s = s.resize((W, round(s.height * W / s.width)), Image.LANCZOS)
            full = Image.new('RGB', (W, H), s.getpixel((6, s.height - 1)))
            full.paste(s.crop((0, 0, W, min(H, s.height))), (0, 0))
            erase_island(full)
            full.save(out / f'{name}-720.webp', quality=80, method=6)
            full.resize((360, 783), Image.LANCZOS).save(out / f'{name}-360.webp', quality=80, method=6)
        print('wrote', out.relative_to(ROOT))


if __name__ == '__main__':
    main(Path(sys.argv[1]))
