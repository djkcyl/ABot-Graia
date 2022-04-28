from io import BytesIO
from pathlib import Path
from loguru import logger

from PIL import Image, ImageDraw, ImageFont

image_path = Path(__file__).parent.joinpath("image")
image_path.mkdir(exist_ok=True)
font = ImageFont.truetype("./font/sarasa-mono-sc-regular.ttf", 20)

color_plant = [
    (0, 0, 0),
    (255, 255, 255),
    (170, 170, 170),
    (85, 85, 85),
    (254, 211, 199),
    (255, 196, 206),
    (250, 172, 142),
    (255, 139, 131),
    (244, 67, 54),
    (233, 30, 99),
    (226, 102, 158),
    (156, 39, 176),
    (103, 58, 183),
    (63, 81, 181),
    (0, 70, 112),
    (5, 113, 151),
    (33, 150, 243),
    (0, 188, 212),
    (59, 229, 219),
    (151, 253, 220),
    (22, 115, 0),
    (55, 169, 60),
    (137, 230, 66),
    (215, 255, 7),
    (255, 246, 209),
    (248, 203, 140),
    (255, 235, 59),
    (255, 193, 7),
    (255, 152, 0),
    (255, 87, 34),
    (184, 63, 39),
    (121, 85, 72),
]


if image_path.joinpath("full.png").exists():
    full_image = Image.open(image_path.joinpath("full.png"))
else:
    full_image = Image.new("RGB", (1024, 1024), (255, 255, 255))
    full_image.save(image_path.joinpath("full.png"))


# 绘制圆形色块，每行 8 个
color_plant_img = Image.new("RGB", (1000, 800), (255, 255, 255))
line = 0
draw = ImageDraw.Draw(color_plant_img)
text_font = ImageFont.truetype("./font/sarasa-mono-sc-regular.ttf", 50)
for i, color in enumerate(color_plant):
    # 当 i 能被 8 整除时，绘制一行
    if i % 8 == 0:
        line += 1
    draw.ellipse(
        (
            (i % 8) * 100 + 20 * (i % 8 + 1),
            (line - 1) * 100 + 90 * (line),
            (i % 8 + 1) * 100 + 20 * (i % 8 + 1),
            (line) * 100 + 90 * (line),
        ),
        fill=color,
        outline="black",
        width=3,
    )
    draw.text(
        (
            (i % 8) * 100 + 20 * (i % 8 + 1) + 25,
            (line - 1) * 100 + 90 * (line) - 60,
        ),
        f"0{i+1}" if i + 1 < 10 else f"{i+1}",
        fill="black",
        font=text_font,
    )
color_plant_img.save(image_path.joinpath("color_plant.png"))
color_plant_bio = BytesIO()
color_plant_img.save(color_plant_bio, "png")
color_plant_img = color_plant_bio.getvalue()

place_chunk = {}

logger.info("正在加载画板区块")
for chunk_x in [str(x) for x in range(32)]:
    for chunk_y in [str(x) for x in range(32)]:
        if image_path.joinpath(f"{chunk_x}_{chunk_y}.png").exists():
            img = Image.open(image_path.joinpath(f"{chunk_x}_{chunk_y}.png"))
            if chunk_x in place_chunk:
                place_chunk[chunk_x][chunk_y] = img
            else:
                place_chunk[chunk_x] = {chunk_y: img}
        else:
            img = Image.new("RGB", (32, 32), (255, 255, 255))
            if chunk_x in place_chunk:
                place_chunk[chunk_x][chunk_y] = img
            else:
                place_chunk[chunk_x] = {chunk_y: img}
            img.save(image_path.joinpath(f"{chunk_x}_{chunk_y}.png"))
logger.info("画板区块加载完成")

# 合并画板区块并写入区块号


def merge_chunk():
    logger.info("正在合并区块全图")
    for chunk_x in [str(x) for x in range(32)]:
        for chunk_y in [str(x) for x in range(32)]:
            full_image.paste(
                place_chunk[chunk_x][chunk_y], (int(chunk_x) * 32, int(chunk_y) * 32)
            )

    full_image.save(image_path.joinpath("full.png"))
    full_bio = BytesIO()
    full_image.save(full_bio, "png")
    return full_bio.getvalue()


def get_draw_line(chunk_x: int = None, chunk_y: int = None):
    if chunk_x is not None and chunk_y is not None:
        need_draw = place_chunk[str(chunk_x)][str(chunk_y)].resize(
            (1024, 1024), Image.NEAREST
        )
        title = f"区块：{chunk_x}_{chunk_y}"
    else:
        need_draw = full_image
        title = "全图"

    logger.info("正在绘制棋盘")
    draw = ImageDraw.Draw(need_draw)
    y_line = False
    img = Image.new("RGB", (1224, 1224), (255, 255, 255))
    for chunk_x in [str(x) for x in range(32)]:
        for chunk_y in [str(x) for x in range(32)]:
            if not y_line:
                draw.line(
                    (int(chunk_y) * 32, 0, int(chunk_y) * 32, 1024), fill="black", width=1
                )
        y_line = True
        draw.line((0, int(chunk_x) * 32, 1024, int(chunk_x) * 32), fill="black", width=1)

    img.paste(need_draw, (100, 100))
    draw = ImageDraw.Draw(img)
    draw.line((1124, 100, 1124, 1124), fill="black", width=1)
    draw.line((100, 1124, 1124, 1124), fill="black", width=1)

    for i in range(32):
        t = f"0{i}" if i < 10 else str(i)
        draw.text((74, 106 + i * 32), t, fill="black", font=font)
        draw.text((1130, 106 + i * 32), t, fill="black", font=font)

        draw.text((107 + i * 32, 74), t, fill="black", font=font)
        draw.text((107 + i * 32, 1130), t, fill="black", font=font)

    draw.text((10, 10), title, fill="black", font=font)

    bio = BytesIO()
    img.save(bio, "png")
    return bio.getvalue()


def draw_pixel(chunk_x: int, chunk_y: int, pixel_x: int, pixel_y: int, color: int):
    img = place_chunk[str(chunk_x)][str(chunk_y)]
    draw = ImageDraw.Draw(img)
    draw.point((pixel_x, pixel_y), fill=color_plant[color - 1])
    img.save(image_path.joinpath(f"{chunk_x}_{chunk_y}.png"))
