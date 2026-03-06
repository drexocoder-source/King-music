

import os
import random
import aiohttp
import aiofiles
import traceback
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
from py_yt import VideosSearch
from ShrutiMusic import app
import math

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

CANVAS_W, CANVAS_H = 1320, 760

FONT_REGULAR_PATH = "ShrutiMusic/assets/font2.ttf"
FONT_BOLD_PATH = "ShrutiMusic/assets/font3.ttf"
DEFAULT_THUMB = "ShrutiMusic/assets/ShrutiBots.jpg"


def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        if draw.textlength(test_line, font=font) <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)
    
    return lines[:2]


def random_gradient():
    colors = [
        [(15, 12, 41), (48, 43, 99), (36, 36, 62)],
        [(10, 10, 10), (35, 35, 40), (20, 20, 25)],
        [(26, 26, 46), (56, 56, 86), (40, 40, 60)],
        [(20, 25, 35), (45, 50, 70), (30, 35, 50)],
        [(12, 17, 30), (38, 43, 65), (25, 30, 45)],
        [(18, 18, 28), (48, 48, 68), (32, 32, 48)],
        [(8, 15, 25), (28, 40, 55), (18, 28, 40)],
        [(22, 22, 35), (52, 52, 75), (35, 35, 55)],
        [(14, 20, 28), (44, 50, 68), (28, 35, 48)],
        [(16, 14, 38), (46, 44, 88), (30, 28, 60)],
    ]
    return random.choice(colors)


def apply_gradient(canvas, colors):
    overlay = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    for y in range(CANVAS_H):
        progress = y / CANVAS_H
        
        if progress < 0.4:
            t = progress / 0.4
            r = int(colors[0][0] * (1-t) + colors[1][0] * t)
            g = int(colors[0][1] * (1-t) + colors[1][1] * t)
            b = int(colors[0][2] * (1-t) + colors[1][2] * t)
        else:
            t = (progress - 0.4) / 0.6
            r = int(colors[1][0] * (1-t) + colors[2][0] * t)
            g = int(colors[1][1] * (1-t) + colors[2][1] * t)
            b = int(colors[1][2] * (1-t) + colors[2][2] * t)
        
        draw.line([(0, y), (CANVAS_W, y)], fill=(r, g, b, 255))
    
    return Image.alpha_composite(canvas, overlay)


def random_layout():
    layouts = [
        {
            'art_size': random.randint(420, 520),
            'art_x': random.randint(60, 120),
            'art_shape': random.choice(['circle', 'rounded', 'diamond']),
            'text_align': 'right',
            'accent_style': random.choice(['line', 'dot', 'wave']),
            'show_particles': random.choice([True, False])
        },
        {
            'art_size': random.randint(400, 500),
            'art_x': CANVAS_W - random.randint(520, 620),
            'art_shape': random.choice(['circle', 'rounded', 'square']),
            'text_align': 'left',
            'accent_style': random.choice(['line', 'glow', 'none']),
            'show_particles': random.choice([True, False])
        },
        {
            'art_size': random.randint(380, 480),
            'art_x': random.randint(80, 140),
            'art_shape': random.choice(['circle', 'hexagon', 'rounded']),
            'text_align': 'right',
            'accent_style': random.choice(['dot', 'wave', 'glow']),
            'show_particles': random.choice([True, False])
        }
    ]
    return random.choice(layouts)


def create_shape_mask(size, shape):
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    
    if shape == 'circle':
        draw.ellipse([0, 0, size, size], fill=255)
    elif shape == 'rounded':
        radius = random.randint(40, 80)
        draw.rounded_rectangle([0, 0, size, size], radius=radius, fill=255)
    elif shape == 'square':
        draw.rectangle([0, 0, size, size], fill=255)
    elif shape == 'diamond':
        points = [(size//2, 0), (size, size//2), (size//2, size), (0, size//2)]
        draw.polygon(points, fill=255)
    elif shape == 'hexagon':
        center = size // 2
        radius = size // 2 - 10
        points = []
        for i in range(6):
            angle = math.pi / 3 * i
            x = center + radius * math.cos(angle)
            y = center + radius * math.sin(angle)
            points.append((x, y))
        draw.polygon(points, fill=255)
    
    return mask


def random_accent_color():
    colors = [
        (88, 166, 255),
        (138, 180, 248),
        (156, 163, 255),
        (200, 200, 220),
        (180, 190, 254),
        (120, 200, 255),
        (165, 177, 255),
        (255, 170, 128),
        (255, 138, 180),
        (148, 226, 213),
    ]
    return random.choice(colors)


def add_particles(draw, accent_color):
    for _ in range(random.randint(15, 30)):
        x = random.randint(0, CANVAS_W)
        y = random.randint(0, CANVAS_H)
        size = random.randint(1, 4)
        alpha = random.randint(40, 120)
        draw.ellipse([x, y, x+size, y+size], fill=(*accent_color, alpha))


def add_accent_elements(draw, layout, accent_color):
    style = layout['accent_style']
    
    if style == 'line':
        y_pos = random.randint(100, 200)
        x_start = random.randint(30, 100)
        length = random.randint(200, 400)
        width = random.randint(2, 4)
        draw.line([(x_start, y_pos), (x_start + length, y_pos)], 
                 fill=(*accent_color, 180), width=width)
    
    elif style == 'dot':
        for _ in range(random.randint(3, 8)):
            x = random.randint(40, CANVAS_W - 40)
            y = random.randint(40, CANVAS_H - 40)
            size = random.randint(4, 10)
            draw.ellipse([x, y, x+size, y+size], fill=(*accent_color, 100))
    
    elif style == 'wave':
        y_start = random.randint(80, 150)
        for x in range(0, CANVAS_W, 3):
            wave_y = y_start + int(math.sin(x / 50) * 20)
            draw.ellipse([x, wave_y, x+2, wave_y+2], fill=(*accent_color, 60))


def add_glow_ring(canvas, x, y, size, color, blur_amount):
    ring_size = size + 30
    ring_img = Image.new("RGBA", (ring_size, ring_size), (0, 0, 0, 0))
    rdraw = ImageDraw.Draw(ring_img)
    
    for i in range(5):
        offset = i * 5
        alpha = 150 - (i * 30)
        rdraw.ellipse([offset, offset, ring_size - offset, ring_size - offset],
                     outline=(*color, alpha), width=3)
    
    ring_img = ring_img.filter(ImageFilter.GaussianBlur(blur_amount))
    canvas.paste(ring_img, (x - 15, y - 15), ring_img)


async def gen_thumb(videoid: str):
    url = f"https://www.youtube.com/watch?v={videoid}"
    thumb_path = None

    try:
        results = VideosSearch(url, limit=1)
        result = (await results.next())["result"][0]

        title = result.get("title", "Unknown Title")
        duration = result.get("duration", "0:00")
        thumburl = result["thumbnails"][0]["url"].split("?")[0]
        channel = result.get("channel", {}).get("name", "")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(thumburl) as resp:
                    if resp.status == 200:
                        thumb_path = CACHE_DIR / f"thumb_{videoid}.png"
                        async with aiofiles.open(thumb_path, "wb") as f:
                            await f.write(await resp.read())
        except:
            pass

        if thumb_path and thumb_path.exists():
            base_img = Image.open(thumb_path).convert("RGBA")
        else:
            base_img = Image.open(DEFAULT_THUMB).convert("RGBA")

    except:
        base_img = Image.open(DEFAULT_THUMB).convert("RGBA")
        title = "King Music"
        duration = "0:00"
        channel = "Music Player"

    try:

        canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H))
        draw = ImageDraw.Draw(canvas)

        # ---------- BACKGROUND ----------
        bg = base_img.resize((CANVAS_W, CANVAS_H))
        bg = bg.filter(ImageFilter.GaussianBlur(100))
        bg = ImageEnhance.Brightness(bg).enhance(0.30)

        canvas.paste(bg, (0, 0))

        overlay = Image.new("RGBA", (CANVAS_W, CANVAS_H), (10, 10, 20, 200))
        canvas = Image.alpha_composite(canvas, overlay)

        draw = ImageDraw.Draw(canvas)

        # ---------- GLASSMORPHISM CARD ----------
        card_w = 900
        card_h = 560

        card_x = (CANVAS_W - card_w) // 2
        card_y = (CANVAS_H - card_h) // 2

        glass_bg = bg.crop((card_x, card_y, card_x + card_w, card_y + card_h))
        glass_bg = glass_bg.filter(ImageFilter.GaussianBlur(35))

        glass = Image.new("RGBA", (card_w, card_h), (30, 30, 40, 140))
        glass_bg = Image.alpha_composite(glass_bg.convert("RGBA"), glass)

        mask = Image.new("L", (card_w, card_h), 0)
        mdraw = ImageDraw.Draw(mask)
        mdraw.rounded_rectangle((0, 0, card_w, card_h), 60, fill=255)

        canvas.paste(glass_bg, (card_x, card_y), mask)

        # ---------- ALBUM ART ----------
        art_size = 300
        art = base_img.resize((art_size, art_size))

        art_mask = Image.new("L", (art_size, art_size), 0)
        adraw = ImageDraw.Draw(art_mask)
        adraw.rounded_rectangle((0, 0, art_size, art_size), 45, fill=255)
        art.putalpha(art_mask)

        art_x = CANVAS_W // 2 - art_size // 2
        art_y = card_y + 40

        # glow
        glow = Image.new("RGBA", (art_size + 80, art_size + 80), (0, 0, 0, 0))
        gdraw = ImageDraw.Draw(glow)
        gdraw.ellipse((0, 0, art_size + 80, art_size + 80), fill=(255, 200, 120, 60))
        glow = glow.filter(ImageFilter.GaussianBlur(40))

        canvas.paste(glow, (art_x - 40, art_y - 40), glow)
        canvas.paste(art, (art_x, art_y), art)

        # ---------- HEADPHONE ICON ----------
        icon_font = ImageFont.truetype(FONT_BOLD_PATH, 60)

        draw.text(
            (card_x + 40, card_y + 30),
            "🎧",
            font=icon_font,
            fill=(255, 220, 150)
        )

        # ---------- FONTS ----------
        title_font = ImageFont.truetype(FONT_BOLD_PATH, 58)
        meta_font = ImageFont.truetype(FONT_REGULAR_PATH, 32)
        small_font = ImageFont.truetype(FONT_REGULAR_PATH, 26)

        # ---------- NOW PLAYING ----------
        now = "NOW PLAYING"

        w = draw.textlength(now, font=small_font)

        draw.text(
            (CANVAS_W // 2 - w // 2, art_y + art_size + 10),
            now,
            fill=(180, 180, 180),
            font=small_font
        )

        # ---------- TITLE ----------
        title = title[:34]

        w = draw.textlength(title, font=title_font)

        draw.text(
            (CANVAS_W // 2 - w // 2, art_y + art_size + 50),
            title,
            fill=(255, 255, 255),
            font=title_font
        )

        # ---------- CHANNEL ----------
        ch = f"{channel}"

        w = draw.textlength(ch, font=meta_font)

        draw.text(
            (CANVAS_W // 2 - w // 2, art_y + art_size + 120),
            ch,
            fill=(200, 200, 200),
            font=meta_font
        )

        # ---------- PROGRESS BAR (GRADIENT) ----------
        bar_w = 640
        bar_h = 12

        bar_x = CANVAS_W // 2 - bar_w // 2
        bar_y = art_y + art_size + 190

        draw.rounded_rectangle(
            (bar_x, bar_y, bar_x + bar_w, bar_y + bar_h),
            20,
            fill=(80, 80, 80)
        )

        progress = int(bar_w * 0.45)

        for i in range(progress):
            r = int(255 - (i / progress) * 120)
            g = int(120 + (i / progress) * 80)
            b = 255
            draw.line(
                [(bar_x + i, bar_y), (bar_x + i, bar_y + bar_h)],
                fill=(r, g, b)
            )

        draw.ellipse(
            (bar_x + progress - 8, bar_y - 4, bar_x + progress + 8, bar_y + 16),
            fill=(255, 255, 255)
        )

        # ---------- TIME ----------
        draw.text(
            (bar_x, bar_y + 22),
            "1:10",
            fill=(210, 210, 210),
            font=small_font
        )

        draw.text(
            (bar_x + bar_w - 60, bar_y + 22),
            duration,
            fill=(210, 210, 210),
            font=small_font
        )

        # ---------- PLAYER CONTROLS ----------
        center_y = bar_y + 90

        draw.polygon(
            [
                (CANVAS_W // 2 - 100, center_y),
                (CANVAS_W // 2 - 70, center_y - 20),
                (CANVAS_W // 2 - 70, center_y + 20)
            ],
            fill=(230, 230, 230)
        )

        draw.ellipse(
            (
                CANVAS_W // 2 - 40,
                center_y - 40,
                CANVAS_W // 2 + 40,
                center_y + 40
            ),
            fill=(255, 200, 120)
        )

        draw.polygon(
            [
                (CANVAS_W // 2 - 8, center_y - 16),
                (CANVAS_W // 2 - 8, center_y + 16),
                (CANVAS_W // 2 + 20, center_y)
            ],
            fill=(20, 20, 20)
        )

        draw.polygon(
            [
                (CANVAS_W // 2 + 100, center_y),
                (CANVAS_W // 2 + 70, center_y - 20),
                (CANVAS_W // 2 + 70, center_y + 20)
            ],
            fill=(230, 230, 230)
        )

        # ---------- WATERMARK ----------
        watermark = "King Music"

        w = draw.textlength(watermark, font=small_font)

        draw.text(
            (CANVAS_W - w - 40, CANVAS_H - 40),
            watermark,
            fill=(180, 180, 180),
            font=small_font
        )

        # ---------- SAVE ----------
        out = CACHE_DIR / f"{videoid}_final.png"

        canvas.save(out)

        if thumb_path and thumb_path.exists():
            os.remove(thumb_path)

        return str(out)

    except Exception as e:
        print(e)
        traceback.print_exc()
        return None
