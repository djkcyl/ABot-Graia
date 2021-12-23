import random

from io import BytesIO
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


FONT_PATH = Path("./font")
font24 = ImageFont.truetype(str(FONT_PATH.joinpath("sarasa-mono-sc-semibold.ttf")), 24)


def draw_game(data):
    player_count = len(data["player"])
    arena_size = (500, (player_count * 50))
    name_size = (player_count * 26) + ((player_count - 1) * 4)
    img_size = (arena_size[0], arena_size[1] + name_size + 60)
    name_text = "\n".join(
        [
            f"{player['horse']} 号马：{player['name']}"
            for _, player in data["player"].items()
        ]
    )
    grass_color = [
        (108, 177, 0),
        (127, 185, 36),
        (108, 177, 0),
        (127, 185, 36),
        (108, 177, 0),
        (127, 185, 36),
    ]
    horse_name = ["①", "②", "③", "④", "⑤", "⑥"]
    image = Image.new("RGB", img_size, (255, 255, 255))
    draw = ImageDraw.Draw(image)

    for i, player in enumerate(data["player"], 0):
        draw.rectangle(
            (20, 20 + (50 * i), 480, 20 + (50 * (i + 1))), fill=grass_color[i]
        )
        for n in range(11):
            draw.line(
                (
                    20 + (46 * n),
                    20 + (50 * i),
                    20 + (46 * n),
                    20 + (50 * (i + 1)),
                ),
                fill=(80, 80, 80),
            )
        draw.text(
            (32 + (data["player"][player]["score"] * 4.14), 32 + (50 * i)),
            horse_name[data["player"][player]["horse"] - 1],
            font=font24,
            fill=(0, 0, 0),
        )
    draw.line((20, 20, 480, 20), fill=(80, 80, 80))
    draw.line(
        (20, 20 + (50 * player_count), 480, 20 + (50 * player_count)), fill=(80, 80, 80)
    )
    draw.line(
        (0, arena_size[1] + 40, img_size[0], arena_size[1] + 40), fill="black", width=2
    )
    draw.text((10, arena_size[1] + 45), name_text, (0, 0, 0), font=font24)
    bio = BytesIO()
    image.save(bio, "jpeg")
    return bio.getvalue()


def run_game(data):
    for player in data["player"]:
        data["player"][player]["score"] += random.randint(8, 18) * random.uniform(
            0.7, 1.2
        )
    return data
