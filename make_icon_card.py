#!/usr/bin/env python3
"""Generate a square icon card with a 3D beveled border and a caption.

Usage:
    python3 make_icon_card.py <image> "<caption>" [-o output.png] [-s 512]
                              [--no-webp] [--webp-quality 80]

By default, also writes a `.webp` next to the PNG (web-optimized). The PNG is
the print-ready master (carries DPI + sRGB ICC profile); the WebP is what the
website serves.
"""

import argparse
import math
import os
import re
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops, ImageEnhance, ImageCms


def caption_from_filename(path):
    """Derive a human caption from a filename.

    Strips decorative bits like ``_Icon`` / ``(iconV2)`` / trailing ``_s``,
    swaps separators for spaces, and inserts spaces at camelCase boundaries.
    """
    stem = os.path.splitext(os.path.basename(path))[0]
    stem = re.sub(r"[\s_]*\(?icon[^)]*\)?$", "", stem, flags=re.IGNORECASE)
    stem = re.sub(r"[\s_]+s$", "", stem)
    stem = stem.replace("_", " ").replace("-", " ")
    stem = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", stem)
    return stem.strip() or "Untitled"


def find_sibling_logo(image_path):
    """Return path of a Logo.webp/png/jpg next to the icon, if any (case-insensitive)."""
    parent = os.path.dirname(os.path.abspath(image_path))
    target = os.path.abspath(image_path)
    try:
        entries = os.listdir(parent)
    except OSError:
        return None
    for name in entries:
        stem, ext = os.path.splitext(name)
        if stem.lower() == "logo" and ext.lower() in (".webp", ".png", ".jpg", ".jpeg"):
            candidate = os.path.join(parent, name)
            if os.path.abspath(candidate) != target:
                return candidate
    return None


def paste_logo(canvas, logo_path, content_box, band_height):
    """Paste a rotated game logo as a corner sticker in the top-right of the panel.

    The logo is sized to fit within ``band_height`` (pre-rotation), rotated 45°
    clockwise, given a gravity-aligned drop shadow, and placed inside the
    panel's top-right with a small margin so it stays clear of the rounded
    corner.
    """
    logo = Image.open(logo_path).convert("RGBA")
    x0, y0, x1, _ = content_box
    avail_w = x1 - x0
    pad_x = int(avail_w * 0.08)
    pad_y = int(band_height * 0.12)
    max_w = max(1, avail_w - 2 * pad_x)
    max_h = max(1, band_height - 2 * pad_y)
    scale = min(max_w / logo.width, max_h / logo.height)
    new_size = (max(1, int(logo.width * scale)), max(1, int(logo.height * scale)))
    logo = logo.resize(new_size, Image.LANCZOS)
    logo = logo.filter(ImageFilter.UnsharpMask(radius=2, percent=120, threshold=2))

    # No rotation — keep the logo upright as a corner badge.
    rotated = logo

    # Position inside the panel's top-right with margin clear of the rounded corner.
    margin = int(avail_w * 0.015)
    pos = (x1 - rotated.width - margin, y0 + margin)

    # Drop shadow built from the rotated logo so its outline still matches
    # what the viewer sees, but offset down-right (gravity) regardless of rotation.
    shadow_offset = max(2, int(rotated.height * 0.04))
    shadow_blur = max(3, int(rotated.height * 0.05))
    shadow_alpha = rotated.split()[-1].point(lambda v: int(v * 0.75))
    shadow_rgb = Image.new("RGB", rotated.size, (0, 0, 0))
    shadow = Image.merge("RGBA", (*shadow_rgb.split(), shadow_alpha))

    shadow_canvas = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow_canvas.alpha_composite(shadow, dest=(pos[0] + shadow_offset, pos[1] + shadow_offset))
    shadow_canvas = shadow_canvas.filter(ImageFilter.GaussianBlur(radius=shadow_blur))
    canvas.alpha_composite(shadow_canvas)

    canvas.alpha_composite(rotated, dest=pos)


def find_font(size):
    candidates = [
        "/System/Library/Fonts/Supplemental/Impact.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def _dim(color, amount):
    rgb = tuple(max(0, c - amount) for c in color[:3])
    return rgb + ((color[3],) if len(color) == 4 else ())


def draw_beveled_frame(canvas, border, radius, panel_mask, miter_blur):
    """Paint a fancy gold bevel: directional shading + bright inner rim highlight.

    The four base color regions are drawn as triangles meeting at the canvas
    center (same 45° miter angles as a trapezoid layout, just extended inward
    so the layer has no transparent gaps). A Gaussian blur softens the miter
    seams. A bright "polished metal" rim is then drawn just outside the panel
    boundary so the inner edge catches a highlight. Applying the sharp
    inverse-panel mask *after* blur keeps the rounded inner edge crisp.
    """
    w, h = canvas.size
    cx, cy = w / 2, h / 2

    # Gold palette — bright top, deep bronze bottom for strong directional sheen.
    top_gold = (255, 235, 150, 255)
    left_gold = (210, 160, 55, 255)
    right_gold = (150, 100, 30, 255)
    bottom_gold = (75, 45, 15, 255)
    rim_gold = (255, 245, 200, 255)

    frame = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(frame)
    d.polygon([(0, 0), (w, 0), (cx, cy)], fill=top_gold)        # top
    d.polygon([(0, 0), (cx, cy), (0, h)], fill=left_gold)        # left
    d.polygon([(w, 0), (cx, cy), (w, h)], fill=right_gold)       # right
    d.polygon([(0, h), (cx, cy), (w, h)], fill=bottom_gold)      # bottom

    if miter_blur > 0:
        frame = frame.filter(ImageFilter.GaussianBlur(radius=miter_blur))

    # Bright "polished" rim hugging the inner edge of the bevel.
    rim_inset = max(2, int(border * 0.18))
    rim_width = max(2, int(border * 0.10))
    rim_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(rim_layer).rounded_rectangle(
        [
            border - rim_inset,
            border - rim_inset,
            w - border + rim_inset,
            h - border + rim_inset,
        ],
        radius=radius + rim_inset,
        outline=rim_gold,
        width=rim_width,
    )
    rim_layer = rim_layer.filter(ImageFilter.GaussianBlur(radius=max(1, miter_blur * 0.25)))
    frame.alpha_composite(rim_layer)

    # Thin dark line on the very outer edge for crisp definition against backgrounds.
    edge_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(edge_layer).rectangle(
        [0, 0, w - 1, h - 1], outline=(40, 25, 5, 255), width=max(1, int(border * 0.05))
    )
    frame.alpha_composite(edge_layer)

    outside = ImageChops.invert(panel_mask)
    frame.putalpha(ImageChops.multiply(frame.split()[-1], outside))
    canvas.alpha_composite(frame)


def build_panel_mask(size, box, radius):
    """Grayscale mask: 255 inside the rounded inner panel, 0 outside."""
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(box, radius=radius, fill=255)
    return mask


def draw_gradient_panel(canvas, box, panel_mask, top_color, bottom_color):
    """Fill the rounded panel with a vertical gradient from top_color to bottom_color."""
    x0, y0, x1, y1 = box
    w = x1 - x0
    h = y1 - y0

    strip = Image.new("RGB", (1, h))
    px = strip.load()
    for i in range(h):
        t = i / max(1, h - 1)
        px[0, i] = (
            int(top_color[0] * (1 - t) + bottom_color[0] * t),
            int(top_color[1] * (1 - t) + bottom_color[1] * t),
            int(top_color[2] * (1 - t) + bottom_color[2] * t),
        )
    grad = strip.resize((w, h)).convert("RGBA")

    panel = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    panel.paste(grad, (x0, y0))
    panel.putalpha(ImageChops.multiply(panel.split()[-1], panel_mask))
    canvas.alpha_composite(panel)


def draw_groove(canvas, box, radius, groove_color):
    ImageDraw.Draw(canvas).rounded_rectangle(
        box, radius=radius, outline=groove_color, width=2
    )


def draw_caption_strip(canvas, content_box, caption_height, panel_mask, strip_color):
    """Straight-topped strip clipped by the panel mask so bottom corners stay rounded."""
    x0, y0, x1, y1 = content_box
    strip_top = y1 - caption_height

    strip = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(strip)
    d.rectangle([x0, strip_top, x1, y1], fill=strip_color)
    # Top-edge shading to feel recessed.
    d.line([(x0, strip_top), (x1, strip_top)], fill=(0, 0, 0, 180), width=1)
    d.line([(x0, strip_top + 1), (x1, strip_top + 1)], fill=(255, 255, 255, 40), width=1)

    # Clip strip alpha by panel mask so rounded bottom corners are respected.
    strip_alpha = strip.split()[-1]
    clipped = ImageChops.multiply(strip_alpha, panel_mask)
    strip.putalpha(clipped)
    canvas.alpha_composite(strip)


def enhance_icon(icon, saturation=1.5, contrast=1.2, brightness=1.05):
    """Boost RGB saturation/contrast/brightness while preserving the alpha channel."""
    r, g, b, a = icon.split()
    rgb = Image.merge("RGB", (r, g, b))
    rgb = ImageEnhance.Color(rgb).enhance(saturation)
    rgb = ImageEnhance.Contrast(rgb).enhance(contrast)
    rgb = ImageEnhance.Brightness(rgb).enhance(brightness)
    r, g, b = rgb.split()
    return Image.merge("RGBA", (r, g, b, a))


def paste_icon(canvas, icon_path, content_box, caption_height, offset_px):
    """Scale the icon to fit, add a soft drop shadow, and composite centered."""
    icon = Image.open(icon_path).convert("RGBA")
    icon = enhance_icon(icon)

    x0, y0, x1, y1 = content_box
    avail_w = x1 - x0
    avail_h = (y1 - y0) - caption_height

    pad = int(min(avail_w, avail_h) * 0.06)
    max_w = avail_w - 2 * pad
    max_h = avail_h - 2 * pad
    scale = min(max_w / icon.width, max_h / icon.height)
    new_size = (max(1, int(icon.width * scale)), max(1, int(icon.height * scale)))
    icon = icon.resize(new_size, Image.LANCZOS)
    # Restore edge crispness lost in the Lanczos downscale.
    icon = icon.filter(ImageFilter.UnsharpMask(radius=2, percent=140, threshold=2))

    cx = x0 + avail_w // 2
    cy = y0 + avail_h // 2
    pos = (cx - new_size[0] // 2 - offset_px, cy - new_size[1] // 2 - offset_px)

    # Soft drop shadow from icon's alpha.
    shadow_offset = max(2, int(min(avail_w, avail_h) * 0.02))
    shadow_blur = max(3, int(min(avail_w, avail_h) * 0.025))
    shadow_alpha = icon.split()[-1].point(lambda v: int(v * 0.55))
    shadow_rgb = Image.new("RGB", icon.size, (0, 0, 0))
    shadow = Image.merge("RGBA", (*shadow_rgb.split(), shadow_alpha))
    shadow_canvas = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow_canvas.alpha_composite(shadow, dest=(pos[0] + shadow_offset, pos[1] + shadow_offset))
    shadow_canvas = shadow_canvas.filter(ImageFilter.GaussianBlur(radius=shadow_blur))
    canvas.alpha_composite(shadow_canvas)

    canvas.alpha_composite(icon, dest=pos)


def draw_caption_text(canvas, text, content_box, caption_height, text_color):
    x0, y0, x1, y1 = content_box
    strip_top = y1 - caption_height

    max_text_w = (x1 - x0) - 20
    max_text_h = caption_height - 12
    lo, hi, best = 10, caption_height, 10
    while lo <= hi:
        mid = (lo + hi) // 2
        font = find_font(mid)
        bbox = font.getbbox(text)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        if tw <= max_text_w and th <= max_text_h:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    font = find_font(best)

    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = x0 + ((x1 - x0) - tw) // 2 - bbox[0]
    ty = strip_top + (caption_height - th) // 2 - bbox[1]

    shadow_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow_layer).text(
        (tx + 2, ty + 2), text, font=font, fill=(0, 0, 0, 180)
    )
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=1.5))
    canvas.alpha_composite(shadow_layer)

    ImageDraw.Draw(canvas).text((tx, ty), text, font=font, fill=text_color)


def build_card(image_path, caption, output_path, size=512, supersample=4, print_cm=3.2,
               webp_quality=80, logo_image_path=None):
    # Render everything at supersample*size, then downscale with Lanczos for AA.
    render_size = size * supersample
    border = max(12, size // 20) * supersample
    radius = max(8, size // 24) * supersample
    caption_height = max(40, size // 7) * supersample
    icon_offset = 0
    miter_blur = border * 0.15  # softens the 45° seams between bevel colors

    panel_top = (255, 252, 245, 255)         # near-white at top for max contrast
    panel_bottom = (200, 208, 220, 255)      # light cool grey at bottom
    caption_color = (38, 42, 50, 255)
    groove = (35, 22, 5, 255)                 # warm dark groove inside the gold rim
    text_color = (255, 225, 140, 255)        # gold caption text

    canvas = Image.new("RGBA", (render_size, render_size), (0, 0, 0, 0))
    content_box = (border, border, render_size - border, render_size - border)
    panel_mask = build_panel_mask(render_size, content_box, radius)

    draw_beveled_frame(canvas, border, radius, panel_mask, miter_blur)
    draw_gradient_panel(canvas, content_box, panel_mask, panel_top, panel_bottom)
    draw_caption_strip(canvas, content_box, caption_height, panel_mask, caption_color)
    draw_groove(canvas, content_box, radius, groove)

    # Icon uses the full panel; the logo (if any) is overlaid as a corner sticker.
    paste_icon(canvas, image_path, content_box, caption_height, icon_offset)
    if logo_image_path:
        avail_h = (content_box[3] - content_box[1]) - caption_height
        logo_band_h = int(avail_h * 0.24)  # 2/3 of the previous (0.36) band size
        paste_logo(canvas, logo_image_path, content_box, logo_band_h)
    draw_caption_text(canvas, caption, content_box, caption_height, text_color)

    if supersample != 1:
        canvas = canvas.resize((size, size), Image.LANCZOS)

    # Print-ready: flatten to RGB (card is fully opaque) and embed sRGB profile
    # so the laser driver interprets colors correctly.
    canvas = canvas.convert("RGB")
    srgb_profile = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()

    dpi = round(size * 2.54 / print_cm)
    canvas.save(output_path, dpi=(dpi, dpi), icc_profile=srgb_profile)

    web_path = None
    if webp_quality is not None:
        web_path = os.path.splitext(output_path)[0] + ".webp"
        canvas.save(web_path, format="WEBP", quality=webp_quality, method=6)

    return output_path, web_path


def main():
    p = argparse.ArgumentParser(description="Generate a 3D-bordered icon card.")
    p.add_argument("image", help="Path to the source icon (webp/png/jpg/...)")
    p.add_argument("caption", nargs="?", help="Caption text (defaults to derived from filename)")
    p.add_argument("-o", "--output", help="Output file path (default: <image>_card.png)")
    p.add_argument("-s", "--size", type=int, default=512, help="Output square size in pixels")
    p.add_argument("--print-cm", type=float, default=3.2, help="Target print size in cm (sets DPI)")
    p.add_argument("--no-webp", action="store_true",
                   help="Skip the .webp web-optimized output (PNG only)")
    p.add_argument("--webp-quality", type=int, default=80,
                   help="WebP quality 1-100 (default 80, visually lossless for these renders)")
    p.add_argument("--logo", help="Path to game logo (auto-detected as Logo.{webp,png,jpg} next to icon)")
    p.add_argument("--no-logo", action="store_true", help="Disable logo overlay even if one is auto-detected")
    args = p.parse_args()

    if not os.path.exists(args.image):
        print(f"error: image not found: {args.image}", file=sys.stderr)
        sys.exit(1)

    output = args.output or os.path.splitext(args.image)[0] + "_card.png"
    caption = args.caption or caption_from_filename(args.image)
    webp_quality = None if args.no_webp else args.webp_quality
    logo_path = None if args.no_logo else (args.logo or find_sibling_logo(args.image))
    png_path, webp_path = build_card(
        args.image, caption, output,
        size=args.size, print_cm=args.print_cm, webp_quality=webp_quality,
        logo_image_path=logo_path,
    )
    print(f"wrote {png_path}")
    if webp_path:
        png_kb = os.path.getsize(png_path) // 1024
        web_kb = os.path.getsize(webp_path) // 1024
        ratio = png_kb / web_kb if web_kb else 0
        print(f"wrote {webp_path}  ({png_kb} KB → {web_kb} KB, {ratio:.1f}× smaller)")


if __name__ == "__main__":
    main()
