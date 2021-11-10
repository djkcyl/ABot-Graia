import httpx

from io import BytesIO
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

from config import yaml_data


AUTH = (
    yaml_data["Saya"]["RecordQuery"]["r6"]["user_id"],
    yaml_data["Saya"]["RecordQuery"]["r6"]["password"],
)
BASEPATH = Path(__file__).parent
DATABASE = BASEPATH.joinpath("data")
DATABASE.joinpath("operators").mkdir(parents=True, exist_ok=True)
DATABASE.joinpath("weapons").mkdir(parents=True, exist_ok=True)
FONT_PATH = Path("font")

# 字体
font_bold_46 = ImageFont.truetype(
    FONT_PATH.joinpath("sarasa-mono-sc-bold.ttf").__str__(), 46
)
font_bold_40 = ImageFont.truetype(
    FONT_PATH.joinpath("sarasa-mono-sc-bold.ttf").__str__(), 40
)
font_bold_32 = ImageFont.truetype(
    FONT_PATH.joinpath("sarasa-mono-sc-bold.ttf").__str__(), 32
)
font_bold_30 = ImageFont.truetype(
    FONT_PATH.joinpath("sarasa-mono-sc-bold.ttf").__str__(), 30
)
font_semibold_24 = ImageFont.truetype(
    FONT_PATH.joinpath("sarasa-mono-sc-semibold.ttf").__str__(), 24
)
font_regular_28 = ImageFont.truetype(
    FONT_PATH.joinpath("sarasa-mono-sc-regular.ttf").__str__(), 28
)
font_regular_24 = ImageFont.truetype(
    FONT_PATH.joinpath("sarasa-mono-sc-regular.ttf").__str__(), 24
)
font_regular_20 = ImageFont.truetype(
    FONT_PATH.joinpath("sarasa-mono-sc-regular.ttf").__str__(), 20
)


text_info = str(
    """\
场均击杀          击杀              死亡              助攻
胜率              胜场              负场              游戏局数
爆头              击倒              破坏              K/D"""
)


def sec_to_minsec(sec):
    minutes, _ = divmod(int(sec), 60)
    hours, minutes = divmod(int(minutes), 60)
    one_min = "%.2f" % (minutes / 60)
    return f"{hours:1d}.{one_min[2]}H"


def circle_corner(img, radii):
    circle = Image.new("L", (radii * 2, radii * 2), 0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, radii * 2, radii * 2), fill=255)

    img = img.convert("RGBA")
    w, h = img.size

    alpha = Image.new("L", img.size, 255)
    alpha.paste(circle.crop((0, 0, radii, radii)), (0, 0))
    alpha.paste(circle.crop((radii, 0, radii * 2, radii)), (w - radii, 0))
    alpha.paste(
        circle.crop((radii, radii, radii * 2, radii * 2)), (w - radii, h - radii)
    )
    alpha.paste(circle.crop((0, radii, radii, radii * 2)), (0, h - radii))
    img.putalpha(alpha)
    return img


def division_zero(a, b):
    if not a or not b:
        return 0
    else:
        return a / b


def inverted_image(image):
    if image.mode == "RGBA":
        r, g, b, a = image.split()
        rgb_image = Image.merge("RGB", (r, g, b))
        inverted_image = ImageOps.invert(rgb_image)
        r2, g2, b2 = inverted_image.split()
        return Image.merge("RGBA", (r2, g2, b2, a))
    else:
        return ImageOps.invert(image)


async def get_pic(type, name):
    PICPATH = DATABASE.joinpath(type, f"{name}.png")
    if PICPATH.exists():
        return Image.open(BytesIO(PICPATH.read_bytes())).convert("RGBA")
    else:
        async with httpx.AsyncClient(timeout=10) as client:
            for _ in range(3):
                try:
                    if type == "operators":
                        r = await client.get(
                            f"https://api.statsdb.net/r6/assets/operators/{name}/figure/small",
                            timeout=10,
                        )
                    elif type == "weapons":
                        r = await client.get(
                            f"https://api.statsdb.net/r6/assets/weapons/{name}",
                            timeout=10,
                        )
                    break
                except httpx.HTTPError:
                    continue
        print(f"图片下载完成：{type} - {name}")
        PICPATH.write_bytes(r.content)
        return Image.open(BytesIO(r.content)).convert("RGBA")


async def draw_r6(nick_name):

    async with httpx.AsyncClient(
        timeout=10, auth=AUTH, follow_redirects=True
    ) as client:
        resp = await client.get(f"https://api.statsdb.net/r6/pc/player/{nick_name}")
        data = resp.json()

    if resp.status_code == 404:
        return

    # hight = 1125
    hight = 1502
    bg = Image.new("RGB", (800, hight), (200, 200, 200))
    draw = ImageDraw.Draw(bg)

    # 渐变背景
    bg_color_form = (80, 80, 80)
    bg_color_to = (40, 40, 40)
    step_r = (bg_color_to[0] - bg_color_form[0]) / hight
    step_g = (bg_color_to[1] - bg_color_form[1]) / hight
    step_b = (bg_color_to[2] - bg_color_form[2]) / hight
    for y in range(0, hight + 1):
        bg_r = round(bg_color_form[0] + step_r * y)
        bg_g = round(bg_color_form[1] + step_g * y)
        bg_b = round(bg_color_form[2] + step_b * y)
        for x in range(0, hight):
            draw.point((x, y), fill=(bg_r, bg_g, bg_b))

    # 用户基本信息
    for _ in range(3):
        try:
            avatar = Image.open(
                BytesIO(httpx.get(data["payload"]["user"]["avatar"]).content)
            )
            break
        except httpx.HTTPError:
            continue
    avatar.thumbnail((128, 128))
    circle_avatar = circle_corner(avatar, 20)
    bg.paste(circle_avatar, (40, 40), circle_avatar)
    draw.text((220, 50), data["payload"]["user"]["nickname"], "white", font_bold_46)
    level = data["payload"]["stats"]["progression"]["level"]
    time = sec_to_minsec(data["payload"]["stats"]["general"]["timeplayed"])
    mmr = data["payload"]["stats"]["seasonal"]["ranked"]["mmr"]
    draw.text(
        (222, 115),
        f"Level {level}   Playtime {time}   MMR {mmr}",
        (200, 200, 200),
        font_regular_28,
    )

    # 战绩板
    record_bg = Image.new("RGB", (720, 380), (26, 27, 31))
    circle_record_bg = circle_corner(record_bg, 12)
    bg.paste(circle_record_bg, (40, 215), circle_record_bg)
    draw.text((80, 250), "全局统计", "white", font_bold_30)

    draw.text((85, 310), text_info, (150, 150, 150), font_regular_20, spacing=70)

    kpm = "%.2f" % division_zero(
        data["payload"]["stats"]["general"]["kills"],
        data["payload"]["stats"]["general"]["matchesplayed"],
    )
    draw.text((180 * 1 - 96, 340), kpm, "white", font_bold_32)
    draw.text(
        (180 * 2 - 94, 340),
        str(data["payload"]["stats"]["general"]["kills"]),
        "white",
        font_bold_32,
    )
    draw.text(
        (180 * 3 - 95, 340),
        str(data["payload"]["stats"]["general"]["deaths"]),
        "white",
        font_bold_32,
    )
    draw.text(
        (180 * 4 - 94, 340),
        str(data["payload"]["stats"]["general"]["assists"]),
        "white",
        font_bold_32,
    )

    wl = "%.2f%%" % (
        data["payload"]["stats"]["general"]["wins"]
        / data["payload"]["stats"]["general"]["matchesplayed"]
        * 100
    )
    draw.text((180 * 1 - 96, 432), wl, "white", font_bold_32)
    draw.text(
        (180 * 2 - 94, 432),
        str(data["payload"]["stats"]["general"]["wins"]),
        "white",
        font_bold_32,
    )
    draw.text(
        (180 * 3 - 95, 432),
        str(data["payload"]["stats"]["general"]["losses"]),
        "white",
        font_bold_32,
    )
    draw.text(
        (180 * 4 - 94, 432),
        str(data["payload"]["stats"]["general"]["matchesplayed"]),
        "white",
        font_bold_32,
    )

    kd = "%.2f" % division_zero(
        data["payload"]["stats"]["general"]["kills"],
        data["payload"]["stats"]["general"]["deaths"],
    )
    draw.text(
        (180 * 1 - 96, 520),
        str(data["payload"]["stats"]["general"]["headshots"]),
        "white",
        font_bold_32,
    )
    draw.text(
        (180 * 2 - 94, 520),
        str(data["payload"]["stats"]["general"]["dbno"]),
        "white",
        font_bold_32,
    )
    draw.text(
        (180 * 3 - 95, 520),
        str(data["payload"]["stats"]["general"]["gadgetdestroy"]),
        "white",
        font_bold_32,
    )
    draw.text((180 * 4 - 94, 520), kd, "white", font_bold_32)

    # 常用干员
    most_played = sorted(
        data["payload"]["stats"]["operators"].copy(),
        key=lambda l1: l1["timeplayed"],
        reverse=True,
    )[0]
    best_kd = sorted(
        data["payload"]["stats"]["operators"].copy(),
        key=lambda l2: (division_zero(l2["kills"], l2["deaths"]), l2["timeplayed"]),
        reverse=True,
    )[0]
    best_wl = sorted(
        data["payload"]["stats"]["operators"].copy(),
        key=lambda l3: (division_zero(l3["wins"], l3["losses"]), l3["timeplayed"]),
        reverse=True,
    )[0]

    operator_box1 = Image.new("RGB", (215, 450), (72, 140, 222))
    operator_box2 = Image.new("RGB", (215, 450), (66, 127, 109))
    operator_box3 = Image.new("RGB", (215, 450), (212, 134, 30))
    operator_figure1 = await get_pic("operators", most_played["id"])
    operator_figure2 = await get_pic("operators", best_kd["id"])
    operator_figure3 = await get_pic("operators", best_wl["id"])
    operator_figure1.thumbnail((600, 850))
    operator_figure2.thumbnail((600, 850))
    operator_figure3.thumbnail((600, 850))
    operator_box1.paste(operator_figure1, (-145, 75), operator_figure1)
    operator_box2.paste(operator_figure2, (-145, 75), operator_figure2)
    operator_box3.paste(operator_figure3, (-145, 75), operator_figure3)
    circle_operator_box1 = circle_corner(operator_box1, 12)
    circle_operator_box2 = circle_corner(operator_box2, 12)
    circle_operator_box3 = circle_corner(operator_box3, 12)
    bg.paste(circle_operator_box1, (40, 635), circle_operator_box1)
    bg.paste(circle_operator_box2, (294, 635), circle_operator_box2)
    bg.paste(circle_operator_box3, (545, 635), circle_operator_box3)

    draw.text((65, 652), "时长最长", "white", font_bold_40)
    draw.text((319, 652), "最佳战绩", "white", font_bold_40)
    draw.text((571, 652), "最佳胜率", "white", font_bold_40)

    draw.text((66, 705), most_played["id"].upper(), "white", font_semibold_24)
    draw.text((320, 705), best_kd["id"].upper(), "white", font_semibold_24)
    draw.text((572, 705), best_wl["id"].upper(), "white", font_semibold_24)

    draw.text(
        (65, 737), sec_to_minsec(most_played["timeplayed"]), "white", font_bold_32
    )
    draw.text(
        (319, 737),
        str(
            "%.2f"
            % division_zero(
                best_kd["kills"], best_kd["deaths"] if best_kd["deaths"] != 0 else 1
            )
        ),
        "white",
        font_bold_32,
    )
    draw.text(
        (571, 737),
        str("%.2f%%" % (division_zero(best_wl["wins"], best_wl["roundsplayed"]) * 100)),
        "white",
        font_bold_32,
    )

    # 常用武器
    weapon_bg = Image.new("RGB", (720, 330), (26, 27, 31))
    circle_weapon_bg = circle_corner(weapon_bg, 12)
    bg.paste(circle_weapon_bg, (40, 1130), circle_weapon_bg)
    draw.text((80, 1165), "最常用的武器", "white", font_bold_30)

    weapons = sorted(
        data["payload"]["stats"]["weaponDetails"].copy(),
        key=lambda lilt: lilt["kills"],
        reverse=True,
    )[0]
    weapons_image = await get_pic("weapons", weapons["key"])
    weapons_image_inverted = inverted_image(weapons_image)
    bg.paste(
        weapons_image_inverted,
        (550 - (weapons_image.size[0] // 2), 1265 - (weapons_image.size[1] // 2)),
        weapons_image_inverted,
    )

    weapon_name_x, _ = font_bold_40.getsize(weapons["name"])
    draw.text((330 - weapon_name_x, 1235), weapons["name"], "white", font_bold_40)

    weapon_kd = "%.2f" % division_zero(
        weapons["kills"], weapons["deaths"] if weapons["deaths"] != 0 else 1
    )
    draw.text(
        (170, 1345), "击杀            爆头            K/D", (150, 150, 150), font_regular_24
    )
    draw.text((172, 1380), str(weapons["kills"]), "white", font_bold_32)
    draw.text((364, 1380), str(weapons["headshots"]), "white", font_bold_32)
    draw.text((554, 1380), str(weapon_kd), "white", font_bold_32)

    bio = BytesIO()
    bg.save(bio, "JPEG")

    return bio.getvalue()
