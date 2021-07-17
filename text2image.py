from PIL import Image,ImageFont,ImageDraw
import re
from io import BytesIO

font_file = 'FZDBSJW.TTF'

async def create_image(text: str):
    imageio = BytesIO()
    text = '\n'.join(await split_text(text))
    height = len(text.split('\n')) + 1
    image = Image.new('RGB', (565, height * 19), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_file, 16)
    draw.text((10, 5), text, font=font, fill='#000000')
    image.save(imageio, format="JPEG", quality=85)
    return imageio


async def split_text(text):
    text = text.strip('\n').split('\n')

    new_text = []
    for item in text:
        if len(item) > 34:
            for sub_item in await cut_code(item, 34):
                if sub_item:
                    new_text.append(sub_item)
        else:
            new_text.append(item)

    return new_text


async def cut_code(code, length):
    code_list = re.findall('.{' + str(length) + '}', code)
    code_list.append(code[(len(code_list) * length):])
    res_list = []
    for n in code_list:
        if n != '':
            res_list.append(n)
    return res_list