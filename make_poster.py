#!/usr/bin/env python3
"""Generate a print-ready A4 poster for Stan's Loot Drop.

Layout (portrait A4, 210x297mm at 300 DPI):
    - Big "STAN'S LOOT" two-tone title (Bungee), LOOT tilted like the site
    - "HANDMADE ROBLOX KEYCHAINS" subline
    - Hero IRL photo of the collection (real/all.webp)
    - Two smaller IRL photos (front/back)
    - Game logo strip (Rivals / Blox Fruits / Adopt Me!)
    - Big QR code linking to https://stansloot.com + URL underneath
    - Yellow marquee strip with the same selling points as the business card

Usage:
    python3 make_poster.py [-o stans_loot_poster.png] [--url https://stansloot.com]
"""

import argparse
import os
import sys

import segno
from PIL import Image, ImageDraw, ImageFilter, ImageCms

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_business_card import (
    FONT_PATHS,
    EMOJI_NATIVE_SIZE,
    font,
    render_emoji_text,
)


# A4 portrait at 300 DPI.
A4_MM = (210, 297)
DPI = 300


def mm_to_px(mm, dpi=DPI):
    return int(round(mm * dpi / 25.4))


def make_qr(url, size_px, dark=(11, 11, 20), light=(255, 255, 255)):
    """Render a QR code at the requested pixel size with the brand palette."""
    import io
    qr = segno.make(url, error="h")  # high error correction so the QR survives the laminating
    module_count = qr.symbol_size(border=2)[0]
    scale = max(1, size_px // module_count)
    buf = io.BytesIO()
    qr.save(
        buf,
        kind="png",
        scale=scale,
        border=2,
        dark="#{:02x}{:02x}{:02x}".format(*dark),
        light="#{:02x}{:02x}{:02x}".format(*light),
    )
    buf.seek(0)
    img = Image.open(buf).convert("RGBA")
    if img.width != size_px:
        img = img.resize((size_px, size_px), Image.NEAREST)
    return img


def paste_image_fit(canvas, img_path, box, *, radius=0, shadow=True, tilt=0):
    """Paste an image scaled to fit a (x0,y0,x1,y1) box, optionally rounded + tilted."""
    x0, y0, x1, y1 = box
    bw, bh = x1 - x0, y1 - y0
    img = Image.open(img_path).convert("RGBA")
    # Cover the box: scale so it fills, then center-crop.
    scale = max(bw / img.width, bh / img.height)
    new_size = (max(1, int(img.width * scale)), max(1, int(img.height * scale)))
    img = img.resize(new_size, Image.LANCZOS)
    cx, cy = img.width // 2, img.height // 2
    img = img.crop((cx - bw // 2, cy - bh // 2, cx - bw // 2 + bw, cy - bh // 2 + bh))

    if radius > 0:
        mask = Image.new("L", (bw, bh), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, bw - 1, bh - 1], radius=radius, fill=255)
        img.putalpha(mask)

    if tilt:
        img = img.rotate(tilt, resample=Image.BICUBIC, expand=True)

    pos = (x0 + (bw - img.width) // 2, y0 + (bh - img.height) // 2)

    if shadow:
        sh_offset = max(4, bh // 60)
        sh_blur = max(6, bh // 40)
        sh_alpha = img.split()[-1].point(lambda v: int(v * 0.55))
        sh_rgb = Image.new("RGB", img.size, (0, 0, 0))
        sh = Image.merge("RGBA", (*sh_rgb.split(), sh_alpha))
        sh_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        sh_layer.alpha_composite(sh, dest=(pos[0] + sh_offset, pos[1] + sh_offset))
        sh_layer = sh_layer.filter(ImageFilter.GaussianBlur(sh_blur))
        canvas.alpha_composite(sh_layer)

    canvas.alpha_composite(img, dest=pos)


def draw_tilted_text(canvas, text, fnt, *, fill, stroke_fill, stroke_w, angle, anchor_xy):
    """Render text to its own layer, rotate, paste centered on anchor_xy."""
    bb = fnt.getbbox(text)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    layer = Image.new("RGBA", (tw + stroke_w * 4, th + stroke_w * 4), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text(
        (-bb[0] + stroke_w * 2, -bb[1] + stroke_w * 2),
        text,
        font=fnt,
        fill=fill,
        stroke_width=stroke_w,
        stroke_fill=stroke_fill,
    )
    if angle:
        layer = layer.rotate(angle, resample=Image.BICUBIC, expand=True)
    pos = (anchor_xy[0] - layer.width // 2, anchor_xy[1] - layer.height // 2)
    canvas.alpha_composite(layer, dest=pos)


def build_poster(output_path, url="https://stansloot.com", supersample=1):
    rs = supersample
    w_out = mm_to_px(A4_MM[0])
    h_out = mm_to_px(A4_MM[1])
    w, h = w_out * rs, h_out * rs

    # Palette (matches the business card / site).
    bg_navy   = (26, 28, 50, 255)
    yellow    = (255, 213, 75, 255)
    coral     = (245, 90, 100, 255)
    white     = (255, 255, 255, 255)
    dark_text = (35, 25, 5, 255)

    inset = int(w * 0.04)
    radius = max(20, w // 24)
    accent_w = max(3, int(w * 0.006))

    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))

    # Solid navy backdrop with rounded corners.
    bg = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(bg).rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=bg_navy)
    canvas.alpha_composite(bg)

    # Subtle radial-glow vignette (yellow at top, pink at bottom-right).
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([-w // 3, -h // 4, w + w // 3, h // 2], fill=(176, 107, 255, 35))
    gd.ellipse([w // 4, h // 2, w + w // 3, h + h // 4], fill=(255, 59, 107, 30))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=w // 8))
    canvas.alpha_composite(glow)

    ix0, iy0 = inset, inset
    ix1, iy1 = w - inset, h - inset
    inner_w = ix1 - ix0
    inner_h = iy1 - iy0

    # ----- measure all blocks first so we can space them evenly ----------
    here = os.path.dirname(os.path.abspath(__file__))

    # 1) Title (STAN'S/LOOT/subline) — fit title size first.
    title_p1 = "STAN'S"
    title_p2 = "LOOT"
    target_w = int(inner_w * 0.58)
    title_size = int(h * 0.085)
    while True:
        title_font = font("bungee", title_size)
        bb1 = title_font.getbbox(title_p1)
        bb2 = title_font.getbbox(title_p2)
        if (max(bb1[2] - bb1[0], bb2[2] - bb2[0]) <= target_w) or title_size < 50:
            break
        title_size -= 6
    line_h = max(title_font.getbbox("LOOT")[3], title_font.getbbox("STAN'S")[3])
    line_gap_inner = -int(line_h * 0.05)
    stroke_w = max(3, int(title_size * 0.06))
    sub = "HANDMADE ROBLOX KEYCHAINS"
    sub_size = int(title_size * 0.22)
    sub_font = font("bungee", sub_size)
    sb = sub_font.getbbox(sub)
    sub_h = sb[3] - sb[1]
    sub_pad_top = int(sub_size * 0.6)
    title_h = line_h * 2 + line_gap_inner + sub_pad_top + sub_h

    # 2) Tilted keychain thumbnails.
    thumb_h = int(inner_h * 0.15)
    thumbs_block_h = thumb_h + int(thumb_h * 0.18)  # extra for tilt overflow

    # 3) Hero IRL photo.
    hero_w = int(inner_w * 0.92)
    hero_h = int(inner_h * 0.18)

    # 4) Logos row (with pill background).
    logos_h = int(inner_h * 0.07)
    pill_pad_x = int(logos_h * 0.45)
    pill_pad_y = int(logos_h * 0.18)
    logos_block_h = logos_h + pill_pad_y * 2

    # 5) QR card — pick the largest square that fits the remaining vertical budget.
    # 6) URL line.
    site = url.replace("https://", "").replace("http://", "").rstrip("/").upper()
    site_max_w = inner_w - int(inner_w * 0.04)
    site_size = int(inner_h * 0.045)
    while True:
        site_font = font("bungee", site_size)
        sb2 = site_font.getbbox(site)
        if (sb2[2] - sb2[0]) <= site_max_w or site_size < 24:
            break
        site_size -= 2
    site_h_px = sb2[3] - sb2[1]

    # Solve for equal gaps: 6 blocks, 5 inter-block gaps inside inner_h.
    # Pick QR size that leaves a nice gap (~3% of inner_h). Clamp to width.
    qr_pad = 0  # will recompute after pick
    target_gap = int(inner_h * 0.03)
    fixed_h = title_h + thumbs_block_h + hero_h + logos_block_h + site_h_px
    qr_card_h = inner_h - fixed_h - target_gap * 5
    qr_card_h = min(qr_card_h, int(inner_w * 0.45))
    qr_card_h = max(qr_card_h, int(inner_w * 0.28))
    qr_size = int(qr_card_h * 0.90)            # the card includes a small pad around the QR
    qr_pad = (qr_card_h - qr_size) // 2
    qr_card_w = qr_card_h

    # Recompute the gap so total height fills inner_h exactly.
    total_h = fixed_h + qr_card_h
    gap = max(0, (inner_h - total_h) // 5)

    # ----- now lay out each block top-down with equal gaps ----------------
    cy = iy0

    # Title
    cx = (ix0 + ix1) // 2
    draw_tilted_text(
        canvas, title_p1, title_font,
        fill=white, stroke_fill=coral, stroke_w=stroke_w, angle=0,
        anchor_xy=(cx, cy + line_h // 2),
    )
    draw_tilted_text(
        canvas, title_p2, title_font,
        fill=yellow, stroke_fill=coral, stroke_w=stroke_w, angle=3,
        anchor_xy=(cx, cy + line_h + line_gap_inner + line_h // 2),
    )
    sub_y = cy + line_h * 2 + line_gap_inner + sub_pad_top
    ImageDraw.Draw(canvas).text(
        ((ix0 + ix1) // 2 - (sb[2] - sb[0]) // 2 - sb[0], sub_y - sb[1]),
        sub, font=sub_font, fill=white,
        stroke_width=max(2, int(sub_size * 0.05)), stroke_fill=coral,
    )
    cy += title_h + gap

    # Tilted keychain cards
    thumbs = [
        (os.path.join(here, "done/Rivals/Knife.png"),               -10),
        (os.path.join(here, "done/BloxFruits/Dragon_Fruit.png"),      4),
        (os.path.join(here, "done/Adopt Me!/Phoenix_.png"),         -6),
    ]
    spread_w = int(inner_w * 0.92)
    spread_x0 = (ix0 + ix1) // 2 - spread_w // 2
    n = len(thumbs)
    anchors = [spread_x0 + int(spread_w * (i + 0.5) / n) for i in range(n)]
    for i, (path, ang) in enumerate(thumbs):
        if not os.path.exists(path):
            continue
        cx_t = anchors[i]
        cy_t = cy + thumb_h // 2 + (int(thumb_h * 0.04) if i == 1 else 0)
        box = (cx_t - thumb_h // 2, cy_t - thumb_h // 2,
               cx_t + thumb_h // 2, cy_t + thumb_h // 2)
        paste_image_fit(canvas, path, box, radius=0, shadow=True, tilt=ang)
    cy += thumbs_block_h + gap

    # Hero IRL photo
    hero_x0 = (ix0 + ix1) // 2 - hero_w // 2
    hero_box = (hero_x0, cy, hero_x0 + hero_w, cy + hero_h)
    paste_image_fit(canvas, os.path.join(here, "real/all.webp"),
                    hero_box, radius=int(hero_h * 0.05))
    cy += hero_h + gap

    # Game logos on pills
    logo_paths = [
        os.path.join(here, "logos/rivals.webp"),
        os.path.join(here, "logos/bloxfruits.webp"),
        os.path.join(here, "logos/adoptme.webp"),
    ]
    logo_imgs = []
    for p in logo_paths:
        if not os.path.exists(p):
            continue
        im = Image.open(p).convert("RGBA")
        scale = logos_h / im.height
        im = im.resize((max(1, int(im.width * scale)), logos_h), Image.LANCZOS)
        logo_imgs.append(im)
    pill_radius = logos_h // 2 + pill_pad_y
    logo_spread_w = int(inner_w * 0.92)
    logo_spread_x0 = (ix0 + ix1) // 2 - logo_spread_w // 2
    n_logos = len(logo_imgs)
    logo_anchors = [
        logo_spread_x0 + int(logo_spread_w * (i + 0.5) / n_logos)
        for i in range(n_logos)
    ]
    logos_top = cy + pill_pad_y  # the icons baseline; pills extend pill_pad_y up and down
    for im, anchor_x in zip(logo_imgs, logo_anchors):
        pill_w = im.width + pill_pad_x * 2
        pill_h = im.height + pill_pad_y * 2
        pill = Image.new("RGBA", (pill_w, pill_h), (0, 0, 0, 0))
        ImageDraw.Draw(pill).rounded_rectangle(
            [0, 0, pill_w - 1, pill_h - 1],
            radius=pill_radius,
            fill=(255, 255, 255, 235),
            outline=coral,
            width=max(2, int(logos_h * 0.05)),
        )
        pill_x = anchor_x - pill_w // 2
        pill_y = logos_top - pill_pad_y
        canvas.alpha_composite(pill, dest=(pill_x, pill_y))
        canvas.alpha_composite(im, dest=(anchor_x - im.width // 2, logos_top))
    cy += logos_block_h + gap

    # QR card
    qr_card_x = (ix0 + ix1) // 2 - qr_card_w // 2
    qr_card_y = cy
    qr_card = Image.new("RGBA", (qr_card_w, qr_card_h), white)
    mask = Image.new("L", (qr_card_w, qr_card_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, qr_card_w - 1, qr_card_h - 1], radius=int(qr_size * 0.06), fill=255
    )
    qr_card.putalpha(mask)
    canvas.alpha_composite(qr_card, dest=(qr_card_x, qr_card_y))
    qr_img = make_qr(url, qr_size, dark=(11, 11, 20), light=(255, 255, 255))
    canvas.alpha_composite(qr_img, dest=(qr_card_x + qr_pad, qr_card_y + qr_pad))

    # Symmetric "SCAN ME" captions on both sides of the QR card.
    cap_font = font("bungee", int(qr_size * 0.13))
    cap_right = "← SCAN ME"
    cap_left = "SCAN ME →"
    cbr = cap_font.getbbox(cap_right)
    cbl = cap_font.getbbox(cap_left)
    cap_gap = int(inner_w * 0.02)
    cap_y_right = qr_card_y + qr_card_h // 2 - (cbr[3] - cbr[1]) // 2 - cbr[1]
    cap_y_left = qr_card_y + qr_card_h // 2 - (cbl[3] - cbl[1]) // 2 - cbl[1]
    cap_x_right = qr_card_x + qr_card_w + cap_gap
    if cap_x_right + (cbr[2] - cbr[0]) <= ix1:
        ImageDraw.Draw(canvas).text(
            (cap_x_right, cap_y_right), cap_right, font=cap_font, fill=yellow,
            stroke_width=max(2, int(qr_size * 0.012)), stroke_fill=coral,
        )
    cap_x_left = qr_card_x - cap_gap - (cbl[2] - cbl[0])
    if cap_x_left >= ix0:
        ImageDraw.Draw(canvas).text(
            (cap_x_left, cap_y_left), cap_left, font=cap_font, fill=yellow,
            stroke_width=max(2, int(qr_size * 0.012)), stroke_fill=coral,
        )
    cy += qr_card_h + gap

    # URL
    ImageDraw.Draw(canvas).text(
        ((ix0 + ix1) // 2 - (sb2[2] - sb2[0]) // 2 - sb2[0], cy - sb2[1]),
        site, font=site_font, fill=white,
        stroke_width=max(2, int(site_size * 0.06)), stroke_fill=coral,
    )

    # ----- thin yellow accent border --------------------------------------
    border = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(border).rounded_rectangle(
        [accent_w // 2, accent_w // 2, w - accent_w // 2 - 1, h - accent_w // 2 - 1],
        radius=radius, outline=yellow, width=accent_w,
    )
    canvas.alpha_composite(border)

    # ----- finish: downscale (if any), embed sRGB + DPI -------------------
    if rs != 1:
        canvas = canvas.resize((w_out, h_out), Image.LANCZOS)
    canvas = canvas.convert("RGB")
    srgb_profile = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    canvas.save(output_path, dpi=(DPI, DPI), icc_profile=srgb_profile)
    return output_path


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-o", "--output", default="stans_loot_poster.png")
    p.add_argument("--url", default="https://stansloot.com",
                   help="Site URL encoded in the QR code (default: https://stansloot.com)")
    args = p.parse_args()
    out = build_poster(args.output, url=args.url)
    print(f"wrote {out}  (A4 portrait, {DPI} DPI, QR -> {args.url})")


if __name__ == "__main__":
    main()
