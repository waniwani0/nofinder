#!/usr/bin/env python3
"""Draw the app icon: a film camera seen head on."""
from PIL import Image, ImageDraw
import os

HERE = os.path.dirname(os.path.abspath(__file__))
S = 1024


def lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def build():
    img = Image.new("RGB", (S, S), (20, 18, 16))
    d = ImageDraw.Draw(img)

    # leatherette body with a soft top light
    for y in range(S):
        t = y / S
        d.line([(0, y), (S, y)], fill=lerp((34, 30, 26), (16, 14, 12), t))

    # chrome top plate
    top, bot = int(S * 0.20), int(S * 0.44)
    stops = [(0.00, (244, 241, 235)), (0.16, (210, 205, 195)),
             (0.46, (163, 158, 149)), (0.60, (188, 183, 173)),
             (0.86, (237, 233, 225)), (1.00, (159, 154, 145))]
    for y in range(top, bot):
        t = (y - top) / (bot - top)
        for i in range(len(stops) - 1):
            a, b = stops[i], stops[i + 1]
            if a[0] <= t <= b[0]:
                d.line([(0, y), (S, y)], fill=lerp(a[1], b[1], (t - a[0]) / (b[0] - a[0])))
                break
    d.line([(0, bot), (S, bot)], fill=(10, 9, 8), width=6)

    # finder window, upper left
    fx, fy, fs = int(S * 0.10), int(S * 0.245), int(S * 0.15)
    d.rounded_rectangle([fx - 8, fy - 8, fx + fs + 8, fy + fs + 8], 14, fill=(22, 19, 15))
    d.rounded_rectangle([fx, fy, fx + fs, fy + fs], 8, fill=(6, 6, 6))
    br = int(fs * 0.22)
    for cx, cy in ((fx, fy), (fx + fs, fy), (fx, fy + fs), (fx + fs, fy + fs)):
        sx = 1 if cx == fx else -1
        sy = 1 if cy == fy else -1
        d.line([(cx + 12 * sx, cy + 12 * sy), (cx + (12 + br) * sx, cy + 12 * sy)], fill=(233, 227, 214), width=6)
        d.line([(cx + 12 * sx, cy + 12 * sy), (cx + 12 * sx, cy + (12 + br) * sy)], fill=(233, 227, 214), width=6)

    # counter window + release button, upper right
    cw = int(S * 0.055)
    ccx, ccy = int(S * 0.70), int(S * 0.32)
    d.ellipse([ccx - cw - 10, ccy - cw - 10, ccx + cw + 10, ccy + cw + 10], fill=(183, 178, 169))
    d.ellipse([ccx - cw, ccy - cw, ccx + cw, ccy + cw], fill=(12, 11, 9))
    d.rectangle([ccx - 5, ccy - cw - 10, ccx + 5, ccy - cw + 12], fill=(168, 65, 44))

    rcx, rcy, rr = int(S * 0.875), int(S * 0.32), int(S * 0.065)
    d.ellipse([rcx - rr, rcy - rr, rcx + rr, rcy + rr], fill=(18, 16, 14))
    d.ellipse([rcx - rr * 0.64, rcy - rr * 0.64, rcx + rr * 0.64, rcy + rr * 0.64], fill=(226, 221, 211))

    # lens barrel
    lcx, lcy = S // 2, int(S * 0.70)
    for r, col in ((int(S * 0.215), (78, 72, 62)), (int(S * 0.198), (154, 145, 132)),
                   (int(S * 0.182), (47, 43, 37))):
        d.ellipse([lcx - r, lcy - r, lcx + r, lcy + r], fill=col)
    br_r = int(S * 0.152)
    d.ellipse([lcx - br_r, lcy - br_r, lcx + br_r, lcy + br_r], fill=(185, 146, 71))
    gr = int(S * 0.138)
    for i in range(gr, 0, -2):
        t = i / gr
        d.ellipse([lcx - i, lcy - i, lcx + i, lcy + i], fill=lerp((10, 14, 16), (51, 71, 74), t ** 3))
    d.ellipse([lcx - int(gr * 0.52), lcy - int(gr * 0.62),
               lcx - int(gr * 0.12), lcy - int(gr * 0.34)], fill=(120, 150, 152))
    return img


def main():
    img = build()
    for size, name in ((512, "icon-512.png"), (192, "icon-192.png"), (180, "apple-touch-icon.png")):
        img.resize((size, size), Image.LANCZOS).save(os.path.join(HERE, name))
        print("wrote", name)


if __name__ == "__main__":
    main()
