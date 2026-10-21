import os
import math
from PIL import Image, ImageDraw

def render_fusion_icon(out_ico: str, out_png: str):
    size = 512
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Base App Squircle: Modern deep obsidian / cosmic glass
    draw.rounded_rectangle(
        [16, 16, size - 16, size - 16],
        radius=110,
        fill=(15, 23, 42, 255),       # #0f172a Deep Slate
        outline=(56, 189, 248, 240),  # #38bdf8 Glowing Cyan Border
        width=10
    )

    # Ambient glows
    glow = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    gdraw.ellipse([50, 60, 260, 450], fill=(66, 133, 244, 45))   # Google blue glow left
    gdraw.ellipse([260, 60, 460, 450], fill=(217, 119, 6, 45))   # Claude terracotta glow right
    img = Image.alpha_composite(img, glow)
    draw = ImageDraw.Draw(img)

    # 2. LEFT SIDE: Antigravity Authentic Logo (White squircle + Google 'A' arch)
    cx, cy = 152, 256
    box_r = 82
    draw.rounded_rectangle(
        [cx - box_r, cy - box_r, cx + box_r, cy + box_r],
        radius=40,
        fill=(255, 255, 255, 255),
        outline=(226, 232, 240, 255),
        width=5
    )

    # Antigravity 'A' parameters
    # Top arch peak at (cx, cy - 50)
    # Left foot at (cx - 46, cy + 48)
    # Right foot at (cx + 46, cy + 48)
    stroke_w = 22

    def quad_bezier(p0, p1, p2, t):
        x = (1-t)**2 * p0[0] + 2*(1-t)*t * p1[0] + t**2 * p2[0]
        y = (1-t)**2 * p0[1] + 2*(1-t)*t * p1[1] + t**2 * p2[1]
        return (x, y)

    # Left side: Green (#34A853) at foot -> Yellow (#FBBC05) -> Red (#EA4335) at peak
    p_foot_l = (cx - 46, cy + 48)
    p_ctrl_l = (cx - 36, cy - 42)
    p_peak = (cx, cy - 50)
    p_ctrl_r = (cx + 36, cy - 42)
    p_foot_r = (cx + 46, cy + 48)

    steps = 40
    for i in range(steps):
        t0 = i / steps
        t1 = (i + 1) / steps
        pt0 = quad_bezier(p_foot_l, p_ctrl_l, p_peak, t0)
        pt1 = quad_bezier(p_foot_l, p_ctrl_l, p_peak, t1)
        if t0 < 0.45:
            c = (52, 168, 83)   # Google Green #34A853
        elif t0 < 0.75:
            c = (251, 188, 5)   # Google Yellow #FBBC05
        else:
            c = (234, 67, 53)   # Google Red #EA4335
        draw.line([pt0, pt1], fill=(*c, 255), width=stroke_w)

    # Right side: Red (#EA4335) at peak -> Blue (#4285F4) down to foot
    for i in range(steps):
        t0 = i / steps
        t1 = (i + 1) / steps
        pt0 = quad_bezier(p_peak, p_ctrl_r, p_foot_r, t0)
        pt1 = quad_bezier(p_peak, p_ctrl_r, p_foot_r, t1)
        if t0 < 0.25:
            c = (234, 67, 53)   # Google Red #EA4335
        elif t0 < 0.55:
            c = (245, 158, 11)  # Warm transition / amber
        else:
            c = (66, 133, 244)  # Google Blue #4285F4
        draw.line([pt0, pt1], fill=(*c, 255), width=stroke_w)

    # Rounded end caps & apex cap
    draw.ellipse([p_peak[0] - stroke_w//2, p_peak[1] - stroke_w//2, p_peak[0] + stroke_w//2, p_peak[1] + stroke_w//2], fill=(234, 67, 53, 255))
    draw.ellipse([p_foot_l[0] - stroke_w//2, p_foot_l[1] - stroke_w//2, p_foot_l[0] + stroke_w//2, p_foot_l[1] + stroke_w//2], fill=(52, 168, 83, 255))
    draw.ellipse([p_foot_r[0] - stroke_w//2, p_foot_r[1] - stroke_w//2, p_foot_r[0] + stroke_w//2, p_foot_r[1] + stroke_w//2], fill=(66, 133, 244, 255))

    # Crossbar: Google Blue (#4285F4)
    bar_y = cy + 10
    bar_x1 = cx - 25
    bar_x2 = cx + 25
    draw.line([(bar_x1, bar_y), (bar_x2, bar_y)], fill=(66, 133, 244, 255), width=stroke_w - 2)
    draw.ellipse([bar_x1 - (stroke_w-2)//2, bar_y - (stroke_w-2)//2, bar_x1 + (stroke_w-2)//2, bar_y + (stroke_w-2)//2], fill=(66, 133, 244, 255))
    draw.ellipse([bar_x2 - (stroke_w-2)//2, bar_y - (stroke_w-2)//2, bar_x2 + (stroke_w-2)//2, bar_y + (stroke_w-2)//2], fill=(66, 133, 244, 255))

    # 3. RIGHT SIDE: Claude Terracotta Asterisk / Star Emblem
    center_r = (360, 256)
    terracotta = (217, 119, 6, 255)       # Claude warm amber/terracotta
    terracotta_bright = (249, 115, 22, 255) # Claude orange

    num_petals = 8
    for i in range(num_petals):
        angle = i * (2 * math.pi / num_petals)
        px = center_r[0] + math.cos(angle) * 78
        py = center_r[1] + math.sin(angle) * 78
        draw.line([center_r, (px, py)], fill=terracotta_bright, width=22)
        draw.ellipse([px - 11, py - 11, px + 11, py + 11], fill=terracotta_bright)

    draw.ellipse([center_r[0] - 44, center_r[1] - 44, center_r[0] + 44, center_r[1] + 44], fill=terracotta)
    draw.ellipse([center_r[0] - 22, center_r[1] - 22, center_r[0] + 22, center_r[1] + 22], fill=(254, 215, 170, 255))

    # 4. Central Transfer Bridge: Glowing Chevron / Arrow Bridge
    arrow_color = (74, 222, 128, 255) # Emerald green
    ax, ay = 256, 256
    for offset_x in [-14, 14]:
        points = [
            (ax + offset_x - 12, ay - 28),
            (ax + offset_x + 12, ay),
            (ax + offset_x - 12, ay + 28)
        ]
        draw.line([points[0], points[1]], fill=arrow_color, width=9)
        draw.line([points[1], points[2]], fill=arrow_color, width=9)

    # Save PNG
    img.save(out_png)

    # Save multi-size ICO
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    icon_images = [img.resize(s, Image.Resampling.LANCZOS) for s in sizes]
    icon_images[0].save(
        out_ico,
        format='ICO',
        sizes=[(s[0], s[1]) for s in sizes],
        append_images=icon_images[1:]
    )
    print(f"ICON CREATED: {out_ico} ({os.path.getsize(out_ico)} bytes)")
    print(f"PNG CREATED: {out_png}")

if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.abspath(__file__))
    render_fusion_icon(
        os.path.join(base_dir, "icon.ico"),
        os.path.join(base_dir, "icon.png")
    )
