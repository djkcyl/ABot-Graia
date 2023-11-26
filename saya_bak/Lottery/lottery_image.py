import httpx
import qrcode
import numpy as np

from io import BytesIO
from pyzbar import pyzbar
from qrcode.image.pil import PilImage
from PIL import Image, ImageDraw, ImageFont

from .certification import encrypt


def qrgen(qq, id, name, period):
    text = encrypt(f"{qq}|{id}|{period}")
    qr = qrcode.QRCode()
    qr.add_data(text)
    image = qr.make_image(PilImage)
    image.thumbnail((500, 500))
    bg = Image.new("RGB", (650, 900), color="white")
    bg.paste(image, ((75, 75)))
    draw = ImageDraw.Draw(bg)
    font_48 = ImageFont.truetype("./saya/Lottery/msyhbd.ttc", 48)
    font_42 = ImageFont.truetype("./saya/Lottery/msyhbd.ttc", 42)
    font_36 = ImageFont.truetype("./saya/Lottery/msyhbd.ttc", 30)
    name = getCutStr(name, 16)
    qq_width = font_48.getsize(qq)
    id_width = font_36.getsize(id)
    name_width = font_42.getsize(name)
    qq_coordinate = int((650 - qq_width[0]) / 2), 740
    name_coordinate = int((650 - name_width[0]) / 2), 680
    id_coordinate = int((650 - id_width[0]) / 2), 600
    draw.text(qq_coordinate, qq, font=font_48, fill="black")
    draw.text(name_coordinate, name, font=font_42, fill="black")
    draw.text(id_coordinate, id, font=font_36, fill="black")
    draw.text((10, 10), f"{period}期", font=font_36, fill="black")
    bg_bio = BytesIO()
    bg.save(bg_bio, format="jpeg")
    return bg_bio.getvalue()


async def qrdecode(url):
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
    image = Image.open(BytesIO(resp.content))
    image_array = np.array(image)
    return pyzbar.decode(image_array)[0].data.decode("utf-8")


def getCutStr(str, cut):
    si = 0
    i = 0
    for s in str:
        si += 1.5 if "\u4e00" <= s <= "\u9fff" else 1
        i += 1
        if si > cut:
            cutStr = str[:i] + "...."
            break
        else:
            cutStr = str

    return cutStr
