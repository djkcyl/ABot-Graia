import asyncio
import re
import time
import httpx

from dataclasses import dataclass

from loguru import logger
from util.browser import get_browser


async def get_result(url, headers):
    async with httpx.AsyncClient() as session:
        for _ in range(3):
            try:
                res = await session.get(url, headers=headers)
                if res.status_code == 200:
                    return res.json()
            except httpx.ReadTimeout:
                logger.warning(f"{url} 请求超时，正在重试")
                await asyncio.sleep(3)
        logger.warning(f"{url} 请求失败")


def remove_xml_tag(text: str):
    return re.compile(r"<[^>]+>", re.S).sub("", text)


def char_seat(char):
    return 0.58 if 32 <= ord(char) <= 126 else 1


@dataclass
class WeiboContent:
    user_name: str
    html_text: str
    pics_list: list
    detail_url: str


# @vivien8261 https://github.com/AmiyaBot/Amiya-Bot/blob/V5-master/functions/weibo/helper.py
class WeiboUser:
    def __init__(self, weibo_id: int):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) "
            "AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.0 Mobile/14E304 Safari/602.1",
            "Content-Type": "application/json; charset=utf-8",
            "Referer": f"https://m.weibo.cn/u/{weibo_id}",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        self.url = "https://m.weibo.cn/api/container/getIndex"
        self.weibo_id = weibo_id
        self.user_name = ""

    def __url(self, container_id=None):
        c_id = f"&containerid={container_id}" if container_id else ""
        return f"{self.url}?type=uid&uid={self.weibo_id}&value={self.weibo_id}{c_id}"

    async def get_user_name(self, result=None):
        if self.user_name:
            return self.user_name

        if not result:
            result = await get_result(self.__url(), self.headers)
        if not result:
            return self.user_name

        if "userInfo" not in result["data"]:
            return self.user_name

        self.user_name = result["data"]["userInfo"]["screen_name"]

        return self.user_name

    async def get_cards_list(self):
        cards = []

        # 获取微博 container id
        result = await get_result(self.__url(), self.headers)
        if not result:
            return cards

        if "tabsInfo" not in result["data"]:
            return cards

        await self.get_user_name(result)

        tabs = result["data"]["tabsInfo"]["tabs"]
        container_id = ""
        for tab in tabs:
            if tab["tabKey"] == "weibo":
                container_id = tab["containerid"]

        # 获取正文列表
        result = await get_result(self.__url(container_id), self.headers)
        if not result:
            return cards

        cards.extend(
            item
            for item in result["data"]["cards"]
            if (
                item["card_type"] == 9
                and "isTop" not in item["mblog"]
                and item["mblog"]["mblogtype"] == 0
            )
        )

        return cards

    async def get_blog_list(self):
        cards = await self.get_cards_list()

        text = ""
        for index, item in enumerate(cards):
            detail = remove_xml_tag(item["mblog"]["text"]).replace("\n", " ").strip()
            length = 0
            content = ""
            for char in detail:
                content += char
                length += char_seat(char)
                if length >= 32:
                    content += "..."
                    break

            date = item["mblog"]["created_at"]
            date = time.strptime(date, "%a %b %d %H:%M:%S +0800 %Y")
            date = time.strftime("%Y-%m-%d %H:%M:%S", date)

            text += f"\n[{index + 1}] {date}\n{content}\n"

        return text

    async def get_weibo_id(self, index: int):
        cards = await self.get_cards_list()
        if cards:
            return cards[index]["mblog"]["bid"]

    async def get_weibo_content(self, index: int):
        cards = await self.get_cards_list()

        if index >= len(cards):
            index = len(cards) - 1

        target_blog = cards[index]
        blog = target_blog["mblog"]
        detail_url = f"https://m.weibo.cn/status/{blog['bid']}"

        # 获取完整正文
        result = await get_result(
            "https://m.weibo.cn/statuses/extend?id=" + blog["id"], self.headers
        )
        if not result:
            return None

        html_text = result["data"]["longTextContent"]
        html_text = re.sub("<br />", "\n", html_text)
        html_text = remove_xml_tag(html_text)
        html_text = html_text.strip("\n")

        # 获取静态图片列表
        pics_list = []
        pics = blog["pics"] if "pics" in blog else []
        for pic in pics:
            pic_url = pic["large"]["url"]
            pics_list.append(pic_url)

        return WeiboContent(self.user_name, html_text, pics_list, detail_url)


class Game:
    def __init__(self):
        self.url = "https://ak-conf.hypergryph.com/config/prod/announce_meta/IOS/announcement.meta.json"

    async def get_announce(self):
        async with httpx.AsyncClient() as client:
            r = await client.get(self.url)
            result = r.json()

        return [x["webUrl"] for x in result["announceList"]]

    async def get_screenshot(self, url):
        async with httpx.AsyncClient() as client:
            r = await client.get(url)
            if "banner-image-container cover" in r.text:
                html = re.search(r'src="(.*)"', r.text)[1]
                img_req = await client.get(html)
                return img_req.content
            else:
                browser = await get_browser()
                page = None
                try:
                    page = await browser.new_page()
                    await page.goto(url, wait_until="networkidle", timeout=10000)
                    await page.set_viewport_size({"width": 500, "height": 273})
                    image = await page.screenshot(full_page=True, type="jpeg", quality=85)
                    await page.close()
                    return image
                except Exception:
                    if page:
                        await page.close()
                    raise
