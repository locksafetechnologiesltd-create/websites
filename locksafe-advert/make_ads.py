"""Build LockSafe ad cards (1080x1920) and transparent phone mockups from app screenshots.

Usage: python3 make_ads.py <screens_dir> <out_dir>
screens_dir must contain come_get_me.webp and stay_with_me.webp (921x2000 screenshots).
"""
import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
BG = (26, 23, 17)
TEAL = (100, 168, 147)
TEAL_DARK = (31, 51, 44)
CREAM = (243, 238, 231)
MUTED = (170, 163, 152)
RED = (211, 97, 85)

FONT_DIR = "/usr/share/fonts/opentype/inter/"


def font(weight, size):
    return ImageFont.truetype(FONT_DIR + {"bold": "InterDisplay-Bold.otf", "semi": "Inter-SemiBold.otf",
                                          "med": "Inter-Medium.otf", "reg": "Inter-Regular.otf"}[weight], size)


def bokeh_bg(seed, warm=True, w=W, h=H):
    """Dark night backdrop with soft streetlight bokeh and film grain."""
    rnd = random.Random(seed)
    img = Image.new("RGB", (w, h), BG)
    glow = Image.new("RGB", (w, h), (0, 0, 0))
    d = ImageDraw.Draw(glow)
    palette = [(255, 170, 80), (255, 140, 60), (255, 205, 140)] if warm else [(100, 168, 147), (70, 120, 160)]
    for _ in range(26):
        r = rnd.randint(30, 120)
        x, y = rnd.randint(-50, w + 50), rnd.randint(-50, int(h * 0.75))
        c = rnd.choice(palette)
        k = rnd.uniform(0.15, 0.45)
        d.ellipse([x - r, y - r, x + r, y + r], fill=tuple(int(v * k) for v in c))
    glow = glow.filter(ImageFilter.GaussianBlur(28))
    img = _add(img, glow)
    # vignette
    vig = Image.new("L", (w, h), 0)
    ImageDraw.Draw(vig).ellipse([-w * 0.3, -h * 0.15, w * 1.3, h * 1.15], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(220))
    img = Image.composite(img, Image.new("RGB", (w, h), (8, 7, 5)), vig)
    return grain(img, seed)


def _add(a, b):
    from PIL import ImageChops
    return ImageChops.add(a, b)


def grain(img, seed, amount=10):
    rnd = random.Random(seed + 99)
    noise = Image.effect_noise(img.size, 40).convert("RGB")
    return Image.blend(img, _add(img, noise.point(lambda v: max(0, v - 128) * amount // 40)), 0.6)


def rounded_mask(size, radius):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius=radius, fill=255)
    return m


def phone(screen, width=560, glow=TEAL):
    """Return an RGBA phone mockup (bezel, rounded screen, soft shadow/glow)."""
    sw = width
    sh = int(screen.height * sw / screen.width)
    scr = screen.convert("RGB").resize((sw, sh), Image.LANCZOS)
    bez = 18
    pw, ph = sw + bez * 2, sh + bez * 2
    pad = 90
    out = Image.new("RGBA", (pw + pad * 2, ph + pad * 2), (0, 0, 0, 0))
    # glow / shadow
    sh_layer = Image.new("RGBA", out.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh_layer).rounded_rectangle([pad - 6, pad + 10, pad + pw + 6, pad + ph + 22], radius=90,
                                               fill=glow + (110,))
    out.alpha_composite(sh_layer.filter(ImageFilter.GaussianBlur(45)))
    body = Image.new("RGBA", (pw, ph), (12, 12, 12, 255))
    bd = ImageDraw.Draw(body)
    bd.rounded_rectangle([0, 0, pw - 1, ph - 1], radius=86, outline=(70, 70, 70, 255), width=3)
    body.putalpha(rounded_mask((pw, ph), 86))
    scr_rgba = scr.convert("RGBA")
    scr_rgba.putalpha(rounded_mask((sw, sh), 70))
    body.alpha_composite(scr_rgba, (bez, bez))
    out.alpha_composite(body, (pad, pad))
    return out


def home_screen(w=921, h=2000):
    """High-res redraw of the LockSafe home screen (Emergency / Come get me / Stay with me)."""
    img = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(img)
    d.text((105, 48), "18:33", font=font("semi", 40), fill=CREAM)
    d.text((42, 170), "LockSafe", font=font("bold", 64), fill=CREAM)
    d.text((42, 262), "✓ 2 verified contacts will be alerted", font=font("reg", 34), fill=TEAL)
    cx, cy, r = w // 2, 830, 300
    for rr, col in [(r + 70, (70, 36, 30)), (r + 45, (120, 52, 44))]:
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=col, width=3)
    # gradient button
    btn = Image.new("RGB", (2 * r, 2 * r))
    bd = ImageDraw.Draw(btn)
    for i in range(2 * r):
        t = i / (2 * r)
        c = tuple(int(a + (b - a) * t) for a, b in zip((236, 128, 112), (178, 66, 56)))
        bd.line([(0, i), (2 * r, i)], fill=c)
    m = Image.new("L", (2 * r, 2 * r), 0)
    ImageDraw.Draw(m).ellipse([0, 0, 2 * r - 1, 2 * r - 1], fill=255)
    img.paste(btn, (cx - r, cy - r), m)
    d.text((cx, cy), "EMERGENCY", font=font("bold", 76), fill=(30, 18, 14), anchor="mm")
    small = font("reg", 30)
    d.text((cx, cy + r + 115), "Press to alert your contacts and share your live", font=small, fill=MUTED, anchor="mm")
    d.text((cx, cy + r + 157), "location with them.", font=small, fill=MUTED, anchor="mm")
    y = 1450
    for label, l1, l2 in [("Come get me", "Not an emergency — a quiet request to one person", "to come to you."),
                          ("Stay with me", "A safety timer for a journey — we alert your contacts", "only if you don't check in.")]:
        d.rounded_rectangle([42, y, w - 42, y + 120], radius=30, outline=TEAL, width=4)
        d.text((cx, y + 60), label, font=font("semi", 42), fill=TEAL, anchor="mm")
        d.text((cx, y + 160), l1, font=font("reg", 28), fill=MUTED, anchor="mm")
        d.text((cx, y + 198), l2, font=font("reg", 28), fill=MUTED, anchor="mm")
        y += 270
    d.text((cx, y + 40), "Trusted contacts", font=font("med", 36), fill=TEAL, anchor="mm")
    return img


def wrap(draw, text, f, maxw):
    words, lines, cur = text.split(), [], ""
    for wd in words:
        t = (cur + " " + wd).strip()
        if draw.textlength(t, font=f) <= maxw:
            cur = t
        else:
            lines.append(cur)
            cur = wd
    lines.append(cur)
    return lines


def text_block(img, y, title, body=None, kicker=None, tsize=92, align="center"):
    d = ImageDraw.Draw(img)
    x = W // 2 if align == "center" else 80
    anchor = "ma" if align == "center" else "la"
    if kicker:
        d.text((x, y), kicker.upper(), font=font("semi", 30), fill=TEAL, anchor=anchor)
        y += 60
    tf = font("bold", tsize)
    for line in title.split("\n"):
        for l in wrap(d, line, tf, W - 160):
            d.text((x, y), l, font=tf, fill=CREAM, anchor=anchor)
            y += int(tsize * 1.12)
    if body:
        y += 24
        bf = font("reg", 40)
        for l in wrap(d, body, bf, W - 180):
            d.text((x, y), l, font=bf, fill=MUTED, anchor=anchor)
            y += 54
    return y


def wordmark(img, y=110, size=46):
    d = ImageDraw.Draw(img)
    f = font("bold", size)
    tw = d.textlength("LockSafe", font=f)
    k = size / 46
    mw, gap = int(38 * k), int(16 * k)
    x = (W - tw - mw - gap) // 2
    # simple shield-dot mark, scaled with the wordmark
    top = y + int(size * 0.18)
    d.rounded_rectangle([x, top, x + mw, top + int(44 * k)], radius=int(12 * k), outline=TEAL, width=max(4, int(5 * k)))
    d.ellipse([x + int(13 * k), top + int(14 * k), x + int(25 * k), top + int(26 * k)], fill=TEAL)
    d.text((x + mw + gap, y), "LockSafe", font=f, fill=CREAM)


def place(img, ph, cx, top):
    img_rgba = img.convert("RGBA")
    img_rgba.alpha_composite(ph, (int(cx - ph.width / 2), int(top)))
    return img_rgba.convert("RGB")


def main(src, out):
    src, out = Path(src), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    cgm = Image.open(src / "come_get_me.webp")
    swm = Image.open(src / "stay_with_me.webp")
    home = home_screen()
    home.save(out / "screen_home_redrawn.png")

    ph_home = phone(home, 560, RED)
    ph_cgm = phone(cgm, 560)
    ph_swm = phone(swm, 560)
    for name, p in [("phone_emergency", ph_home), ("phone_come_get_me", ph_cgm), ("phone_stay_with_me", ph_swm)]:
        p.save(out / f"{name}_transparent.png")

    cards = []

    # 1 hook
    c = bokeh_bg(1)
    wordmark(c)
    text_block(c, 640, "Text me when\nyou get home.", "We all say it. LockSafe makes sure someone actually knows.", tsize=104)
    cards.append(("01_hook", c))

    # 2 emergency
    c = bokeh_bg(2)
    y = text_block(c, 150, "One press.", "Your trusted contacts are alerted with your live location.", kicker="Emergency", tsize=100)
    c = place(c, ph_home, W / 2, y - 40)
    cards.append(("02_emergency", c))

    # 3 come get me
    c = bokeh_bg(3)
    y = text_block(c, 150, "Need out? Quietly.", "Bad date. Wrong party. One hold and Dad's on his way — no call, and the person you're with won't know.", kicker="Come Get Me", tsize=96)
    c = place(c, ph_cgm, W / 2, y - 50)
    cards.append(("03_come_get_me", c))

    # 4 stay with me
    c = bokeh_bg(4)
    y = text_block(c, 150, "Got your back on every journey.", "Set a timer for the run, the dog walk, the walk home. Miss your check-in and your contacts get your location.", kicker="Stay With Me", tsize=88)
    c = place(c, ph_swm, W / 2, y - 50)
    cards.append(("04_stay_with_me", c))

    # 5 privacy
    c = bokeh_bg(5, warm=False)
    wordmark(c)
    text_block(c, 620, "Nobody sees you.\nUntil you\nneed them to.", "Nothing is shared unless you press, ask, or miss a check-in. Your location stays yours.", tsize=92)
    cards.append(("05_privacy", c))

    # 6 three features
    c = bokeh_bg(6)
    text_block(c, 150, "Three ways to\nget home safe.", tsize=96)
    small = [phone(s, 330, g) for s, g in [(cgm, TEAL), (home, RED), (swm, TEAL)]]
    ci = c.convert("RGBA")
    for p, cx, top, rot in [(small[0], 260, 640, 8), (small[2], 820, 640, -8), (small[1], 540, 560, 0)]:
        pr = p.rotate(rot, resample=Image.BICUBIC, expand=True)
        ci.alpha_composite(pr, (int(cx - pr.width / 2), top))
    c = ci.convert("RGB")
    d = ImageDraw.Draw(c)
    for x, t in [(260, "Come Get Me"), (540, "Emergency"), (820, "Stay With Me")]:
        d.text((x, 1530), t, font=font("semi", 36), fill=CREAM, anchor="ma")
    cards.append(("06_three_features", c))

    # 7 end card
    c = bokeh_bg(7)
    d = ImageDraw.Draw(c)
    wordmark(c, y=700, size=110)
    d.text((W / 2, 880), "We hope you never have to use it.", font=font("med", 46), fill=MUTED, anchor="ma")
    d.rounded_rectangle([W / 2 - 300, 1040, W / 2 + 300, 1160], radius=60, fill=TEAL)
    d.text((W / 2, 1100), "Download LockSafe", font=font("semi", 46), fill=(16, 33, 25), anchor="mm")
    cards.append(("07_end_card", c))

    for name, img in cards:
        img.save(out / f"{name}.png", optimize=True)
    return [n for n, _ in cards]


if __name__ == "__main__":
    print(main(sys.argv[1], sys.argv[2]))
