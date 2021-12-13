from io import BytesIO
from pathlib import Path
from loguru import logger
from PIL import Image, ImageDraw, ImageFont


font = ImageFont.truetype(str(Path("./font/sarasa-mono-sc-regular.ttf")), 20)
font_bold = ImageFont.truetype(str(Path("./font/sarasa-mono-sc-bold.ttf")), 24)
font28 = ImageFont.truetype(str(Path("./font/sarasa-mono-sc-regular.ttf")), 28)

tag_color = [(44, 62, 80), (155, 89, 182), (241, 196, 15), (211, 84, 0)]
operator_color = [
    (0, 0, 0),
    (0, 0, 0),
    (0, 0, 0),
    (155, 89, 182),
    (243, 156, 18),
    (211, 84, 0),
]


def draw(recruit_info):
    i = 0
    text_list = []
    for tags, operators, rank in recruit_info:
        try:
            r = operators[0][1]
        except IndexError:
            continue
        if rank:
            i += 1
            text_list.append([f"\n \n{' '.join(tags)}\n", 1, rank])
            for op, rank in operators:
                if r != rank:
                    r = rank
                    text_list.append("\n")
                text_list.append([f"{op} ", 0, rank])

    if not i:
        return

    logger.debug(f"为你找到以下可用的招募方案：\n{''.join([t[0] for t in text_list])}")

    text_x, text_y = font.getsize_multiline(
        f"为你找到以下可用的招募方案：\n{''.join([t[0] for t in text_list])}"
    )
    text_x = max(text_x, 392)

    img = Image.new("RGB", (text_x + 20, text_y + 20), (235, 235, 235))
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), "为你找到以下可用的招募方案：", (33, 33, 33), font=font28)
    h = 24
    i = 2
    for tags, operators, rank in recruit_info:
        try:
            r = operators[0][1]
        except IndexError:
            continue
        if rank:
            tag = " ".join(tags)
            draw.text(
                (10, 4 + (h * i)),
                f"{tag} ★" if len(operators) == 1 else tag,
                tag_color[rank],
                font=font_bold,
            )
            i += 1
            o = 0
            for op, rank in operators:
                if r != rank:
                    r = rank
                    o = 0
                    i += 1
                draw.text((10 + o, 10 + (h * i)), op, operator_color[rank], font=font)
                o += font.getsize(op)[0] + 10
            i += 2

    bio = BytesIO()
    img.save(bio, format="JPEG")
    return bio.getvalue()
