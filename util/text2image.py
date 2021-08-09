import re

from io import BytesIO
from PIL import Image, ImageFont, ImageDraw

from .CutString import get_cut_str

font_file = './font/sarasa-mono-sc-semibold.ttf'
font = ImageFont.truetype(font_file, 18)


async def create_image(text: str, cut=64, transparent=False):
    imageio = BytesIO()
    cut_str = '\n'.join(await get_cut_str(text, cut))
    textx, texty = font.getsize_multiline(cut_str)
    if transparent:
        image = Image.new('RGBA', (textx + 40, texty + 40), (0, 0, 0, 0,))
    else:
        image = Image.new('RGB', (textx + 40, texty + 40), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.text((20, 20), cut_str, font=font, fill='#000000')
    if transparent:
        image.save(imageio, format="PNG")
    else:
        image.save(imageio, format="JPEG", quality=85)
    return imageio
