#!/usr/bin/env python3
"""Arte de contagem regressiva do GTA 6 para o feed (1080x1350, 4:5).

Uso:
  python3 make_poster.py <fundo.png> <saida.png> --numero 4 [--palavra DIAS]
         [--topo "19 DE NOVEMBRO"] [--rodape "PARA O LANÇAMENTO DE GTA 6"] [--x0 940]

<fundo.png> é um frame do trailer (ex.: 3840x1920 sem as faixas pretas).
--x0 escolhe onde começa o recorte 4:5 no frame (em pixels do frame original).
"""
import argparse
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1350
FONT_DIR = "/usr/share/fonts/opentype/inter/"
BLACK = FONT_DIR + "InterDisplay-Black.otf"
LIGHT = FONT_DIR + "InterDisplay-Medium.otf"

# paleta "Vice City": azul -> roxo -> rosa -> laranja
NUM_STOPS = [(0.0, (59, 108, 255)), (0.4, (170, 75, 243)), (0.75, (255, 95, 162)), (1.0, (255, 190, 90))]


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def gradient(size, stops):
    w, h = size
    g = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / max(h - 1, 1)
        for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
            if p0 <= t <= p1:
                g.putpixel((0, y), lerp(c0, c1, (t - p0) / (p1 - p0)))
                break
    return g.resize((w, h))


def spaced(draw, text, y, font, spacing, fill=(255, 255, 255), shadow=True):
    widths = [draw.textlength(ch, font=font) for ch in text]
    total = sum(widths) + spacing * (len(text) - 1)
    x = (W - total) / 2
    for ch, cw in zip(text, widths):
        if shadow:
            draw.text((x + 3, y + 3), ch, font=font, fill=(0, 0, 0, 140))
        draw.text((x, y), ch, font=font, fill=fill)
        x += cw + spacing


def background(path, x0):
    img = Image.open(path).convert("RGB")
    ch = img.height
    cw = int(ch * W / H)
    x0 = max(0, min(x0, img.width - cw))
    img = img.crop((x0, 0, x0 + cw, ch)).resize((W, H), Image.LANCZOS)
    # tom roxo/rosa por cima da cena
    tint = gradient((W, H), [(0, (90, 50, 170)), (0.6, (200, 70, 150)), (1, (60, 20, 80))])
    img = Image.blend(img, tint, 0.22)
    # escurece topo e base para o texto aparecer
    shade = Image.new("L", (1, H))
    for y in range(H):
        t = y / (H - 1)
        a = 150 * max(0, 1 - t / 0.18) + 190 * max(0, (t - 0.55) / 0.45)
        shade.putpixel((0, y), int(min(a, 210)))
    dark = Image.new("RGB", (W, H), (15, 5, 30))
    img.paste(dark, (0, 0), shade.resize((W, H)))
    return img


def big_number(canvas, text, cy, size):
    font = ImageFont.truetype(BLACK, size)
    tmp = ImageDraw.Draw(canvas)
    l, t, r, b = tmp.textbbox((0, 0), text, font=font)
    tw, th = r - l, b - t
    x, y = (W - tw) // 2 - l, cy - th // 2 - t
    # sombra
    sh = Image.new("L", (W, H), 0)
    ImageDraw.Draw(sh).text((x + 14, y + 18), text, font=font, fill=170)
    canvas.paste((0, 0, 0), (0, 0), sh.filter(ImageFilter.GaussianBlur(14)))
    # contorno branco
    ImageDraw.Draw(canvas).text((x, y), text, font=font, fill=(255, 255, 255), stroke_width=12, stroke_fill=(255, 255, 255))
    # preenchimento em degradê
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).text((x, y), text, font=font, fill=255)
    grad = Image.new("RGB", (W, H))
    grad.paste(gradient((tw, th), NUM_STOPS), (x + l, y + t))
    canvas.paste(grad, (0, 0), mask)
    return y + b  # base do número


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("fundo")
    ap.add_argument("saida")
    ap.add_argument("--numero", required=True)
    ap.add_argument("--palavra", default="DIAS")
    ap.add_argument("--topo", default="19 DE NOVEMBRO")
    ap.add_argument("--rodape", default="PARA O LANÇAMENTO DE GTA 6")
    ap.add_argument("--x0", type=int, default=940)
    a = ap.parse_args()

    img = background(a.fundo, a.x0).convert("RGBA")
    d = ImageDraw.Draw(img)
    spaced(d, a.topo, 52, ImageFont.truetype(LIGHT, 44), 14)

    size = 560 if len(a.numero) <= 2 else int(560 * 2.2 / len(a.numero))
    bottom = big_number(img, a.numero, 640, size)

    d = ImageDraw.Draw(img)
    f_word = ImageFont.truetype(BLACK, 170)
    l, t, r, b = d.textbbox((0, 0), a.palavra, font=f_word)
    x, y = (W - (r - l)) // 2 - l, bottom + 20 - t
    d.text((x + 6, y + 8), a.palavra, font=f_word, fill=(0, 0, 0, 160))
    d.text((x, y), a.palavra, font=f_word, fill=(255, 255, 255))
    spaced(d, a.rodape, y + b + 30, ImageFont.truetype(LIGHT, 34), 9)

    img.convert("RGB").save(a.saida, quality=95)
    print("ok ->", a.saida)


if __name__ == "__main__":
    main()
