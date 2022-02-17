from io import BytesIO
from pathlib import Path
from loguru import logger
from PIL import Image, ImageDraw, ImageFont


font = ImageFont.truetype(str(Path("./font/sarasa-mono-sc-regular.ttf")), 20)
font_bold = ImageFont.truetype(str(Path("./font/sarasa-mono-sc-bold.ttf")), 20)
font28 = ImageFont.truetype(str(Path("./font/sarasa-mono-sc-bold.ttf")), 26)

tag_color = [(44, 62, 80), (155, 89, 182), (243, 156, 18), (211, 84, 0)]
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
        if rank > 0:
            i += 1
            tag = " ".join(tags)
            text_list.append([f"\n \n{tag}\n", 1, rank])
            if tag in ["高级资深干员", "资深干员"]:
                text_list.append(["一堆干员任你选", 0, rank])
            else:
                for op, rank in operators:
                    if r != rank:
                        r = rank
                        text_list.append("\n")
                    text_list.append([f"{op} ", 0, rank])

    if not i:
        return

    logger.debug("".join([t[0] for t in text_list]))

    text_x, text_y = font.getsize_multiline("".join([t[0] for t in text_list]))

    img = Image.new("RGB", (text_x + 20, text_y + 30), (235, 235, 235))
    draw = ImageDraw.Draw(img)
    h = 26
    i = 0
    for tags, operators, rank in recruit_info:
        try:
            r = operators[0][1]
        except IndexError:
            continue
        if rank > 0:
            tag = " ".join(tags)
            if rank == 0.5:
                rank = 0
            draw.text(
                (10, 10 + (h * i)),
                f"{tag} ★" if len(operators) == 1 else tag,
                (33, 33, 33),
                # tag_color[rank],
                font=font_bold,
            )
            i += 1
            if tag in ["高级资深干员", "资深干员"]:
                draw.text(
                    (10, 10 + (h * i)),
                    "一堆干员任你选",
                    operator_color[rank + 2],
                    font=font,
                )
            else:
                o = 0
                for op, rank in operators:
                    if r != rank:
                        r = rank
                        o = 0
                        i += 1
                    draw.text(
                        (10 + o, 10 + (h * i)), op, operator_color[rank], font=font
                    )
                    o += font.getsize(op)[0] + 10
            i += 2

    bio = BytesIO()
    img.save(
        bio,
        format="JPEG",
        quality=100,
    )
    return bio.getvalue()
