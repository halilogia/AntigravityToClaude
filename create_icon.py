import os
import math
from PIL import Image, ImageDraw, ImageFilter

def create_fusion_icon(out_path: str):
    size = 512  # Render high-res first, then downsample for ultra-smooth anti-aliasing
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. Rounded App Squircle Background
    # Dark cosmic slate with glowing cyan border
    corner_radius = 110
    draw.rounded_rectangle(
        [16, 16, size - 16, size - 16],
        radius=corner_radius,
        fill=(15, 23, 42, 255),       # #0f172a
        outline=(56, 189, 248, 255),   # #38bdf8 cyan border
        width=10
    )

    # Subtle inner gradient / glow
    inner_glow = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(inner_glow)
    glow_draw.ellipse([80, 80, 432, 432], fill=(6, 182, 212, 35))
    glow_draw.ellipse([140, 140, 372, 372], fill=(217, 119, 6, 45))
    img = Image.alpha_composite(img, inner_glow)
    draw = ImageDraw.Draw(img)

    # 2. Left Element: Antigravity Cosmic Orbital Rings
    center_l = (180, 256)
    draw.ellipse([center_l[0] - 110, center_l[1] - 110, center_l[0] + 110, center_l[1] + 110], outline=(56, 189, 248, 220), width=12)
    draw.ellipse([center_l[0] - 80, center_l[1] - 80, center_l[0] + 80, center_l[1] + 80], outline=(14, 165, 233, 180), width=8)
    # Glowing nucleus core
    draw.ellipse([center_l[0] - 35, center_l[1] - 35, center_l[0] + 35, center_l[1] + 35], fill=(56, 189, 248, 255))
    draw.ellipse([center_l[0] - 18, center_l[1] - 18, center_l[0] + 18, center_l[1] + 18], fill=(255, 255, 255, 255))

    # 3. Right Element: Claude Terracotta Asterisk / Star Emblem
    center_r = (332, 256)
    # Claude terracotta 8-pointed warm star/flower
    terracotta = (217, 119, 6, 255)       # Claude warm amber/terracotta
    terracotta_bright = (249, 115, 22, 255) # Claude orange

    num_petals = 8
    for i in range(num_petals):
        angle = i * (2 * math.pi / num_petals)
        px = center_r[0] + math.cos(angle) * 75
        py = center_r[1] + math.sin(angle) * 75
        draw.line([center_r, (px, py)], fill=terracotta_bright, width=22)

    # Center core of Claude emblem
    draw.ellipse([center_r[0] - 42, center_r[1] - 42, center_r[0] + 42, center_r[1] + 42], fill=terracotta)
    draw.ellipse([center_r[0] - 22, center_r[1] - 22, center_r[0] + 22, center_r[1] + 22], fill=(254, 215, 170, 255))

    # 4. Central Transfer Bridge: Glowing Fast-Forward / Arrow Bridge (Antigravity -> Claude)
    arrow_color = (74, 222, 128, 255) # Emerald green
    ax = 256
    ay = 256
    # Right-pointing double chevron
    for offset_x in [-18, 18]:
        points = [
            (ax + offset_x - 14, ay - 32),
            (ax + offset_x + 14, ay),
            (ax + offset_x - 14, ay + 32)
        ]
        draw.line([points[0], points[1]], fill=arrow_color, width=10)
        draw.line([points[1], points[2]], fill=arrow_color, width=10)

    # Downsample and save as multi-size Windows icon (.ico)
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    icon_images = []
    for s in sizes:
        icon_images.append(img.resize(s, Image.Resampling.LANCZOS))

    icon_images[0].save(
        out_path,
        format='ICO',
        sizes=[(s[0], s[1]) for s in sizes],
        append_images=icon_images[1:]
    )
    print(f"ICON CREATED: {out_path} ({os.path.getsize(out_path)} bytes)")

    # Also save a high-res PNG preview
    png_path = out_path.replace('.ico', '.png')
    img.resize((256, 256), Image.Resampling.LANCZOS).save(png_path)
    print(f"PNG PREVIEW CREATED: {png_path}")

if __name__ == '__main__':
    ico_dest = r"C:\Users\Halil Emre\Desktop\GitHub\Public\AntigravityToClaude\icon.ico"
    create_fusion_icon(ico_dest)
