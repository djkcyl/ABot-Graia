import httpx

from io import BytesIO
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


FONT_PATH = Path('font')


def sec_to_minsec(sec):
    minutes, seconds = divmod(int(sec), 60)
    return f"{minutes:02d}:{seconds:02d}"


async def draw_tracemoe(search_data, media_data):
    title_font = ImageFont.truetype(FONT_PATH.joinpath('sarasa-mono-sc-semibold.ttf').__str__(), 28)
    subtitle_font = ImageFont.truetype(FONT_PATH.joinpath('sarasa-mono-sc-semibold.ttf').__str__(), 18)
    body_font = ImageFont.truetype(FONT_PATH.joinpath('sarasa-mono-sc-regular.ttf').__str__(), 22)

    bg_x = 900

    # 标题
    title_img = Image.new("RGB", (bg_x, 100), "#335fff")
    draw = ImageDraw.Draw(title_img)
    draw.text((17, 15), media_data['title']['native'], "white", title_font)
    draw.text((17, 55), media_data['title']['romaji'], "white", subtitle_font)

    # 封面
    async with httpx.AsyncClient(timeout=10) as client:
        res = await client.get(media_data['coverImage']["large"])
    cover_img = Image.open(BytesIO(res.content))
    coverx, covery = cover_img.size
    if covery < 400:
        ratio = covery / coverx
        cover_img = cover_img.resize((int(400 / ratio), 400))
    else:
        cover_img.thumbnail((1000, 400))

    # 剧集信息
    startDate = '-'.join([str(media_data['startDate'][x]) for x in media_data['startDate']])
    endDate = '-'.join([str(media_data['endDate'][x]) for x in media_data['endDate']])
    airing = f"{startDate} 至 {endDate}"
    try:
        transName = media_data.get('title', {}).get("chinese", " ") + "\n" + media_data.get('title', {}).get("english", " ")
    except:
        transName = ""
    info = f"{media_data['episodes']} episodes {media_data['duration']}-minute {media_data['format']} {media_data['type']}\n播出于 {airing}"
    info_img = Image.new("RGB", (bg_x, 300), 'white')
    draw = ImageDraw.Draw(info_img)
    draw.text((100, 20), info, (50, 50, 50), body_font)
    draw.line(((55, 22), (55, 73)), (100, 100, 100), 8)
    draw.text((45, 110), "译名", (50, 50, 50), title_font)
    draw.text((120, 103), transName, (50, 50, 50), body_font)

    # 识别信息
    search_text = f"出自第 {str(search_data['episode'])} 集\n{sec_to_minsec(search_data['from'])} 至 {sec_to_minsec(search_data['to'])}\n相似度：{'%.2f%%' % (search_data['similarity'] * 100)}"
    search_img = Image.new("RGB", (bg_x, 220), "white")
    if not media_data['isAdult']:
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(search_data['image'])
        screenshot = Image.open(BytesIO(res.content))
        screenshotx, screenshoty = screenshot.size
        if screenshoty < 220:
            ratio = screenshoty / screenshotx
            screenshot = screenshot.resize((int(220 / ratio), 220))
        else:
            screenshot.thumbnail((1000, 220))
        search_img.paste(screenshot, (0, 0))
    draw = ImageDraw.Draw(search_img)
    draw.text((430, 50), search_text, (20, 20, 20), body_font, spacing=12)

    # 输出
    bg = Image.new("RGB", (bg_x, 500), "white")
    bg.paste(title_img, (0, 0))
    bg.paste(info_img, (0, 100))
    bg.paste(search_img, (0, 280))
    if not media_data['isAdult']:
        bg.paste(cover_img, (bg_x - cover_img.size[0], 100))
    bio = BytesIO()
    bg.save(bio, "JPEG")
    return bio.getvalue()

