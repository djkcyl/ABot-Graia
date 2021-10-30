import re
import httpx

from util.browser import get_browser


class Weibo():
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) '
                          'AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.0 Mobile/14E304 Safari/602.1',
            'Content-Type': 'application/json; charset=utf-8',
            'Referer': 'https://m.weibo.cn/u/6279793937',
            'Accept-Language': 'zh-CN,zh;q=0.9'
        }
        self.url = 'https://m.weibo.cn/api/container/getIndex?uid=6279793937&type=uid&value=6279793937'

    async def requests_content(self, index: int, only_id=False):
        cards = await self.get_cards_list()

        target_blog = cards[index]
        blog = target_blog['mblog']
        detail_url = target_blog['scheme']
        item_id = target_blog['itemid']

        if only_id:
            return item_id

        # 获取完整正文
        url = 'https://m.weibo.cn/statuses/extend?id=' + blog['id']

        async with httpx.AsyncClient(headers=self.headers) as client:
            r = await client.get(url)
            result = r.json()

        html_text = result['data']['longTextContent']
        html_text = re.sub('<br />', '\n', html_text)
        html_text = remove_xml_tag(html_text)
        html_text = html_text.strip('\n')

        # 获取静态图片列表
        pics_list = []
        pics = blog['pics'] if 'pics' in blog else []
        for pic in pics:
            pic_url = pic['large']['url']
            pics_list.append(pic_url)

        return html_text, detail_url, pics_list

    async def get_cards_list(self):
        cards = []

        # 获取微博 container id
        async with httpx.AsyncClient(headers=self.headers) as client:
            r = await client.get(self.url)
            result = r.json()

            if 'tabsInfo' not in result['data']:
                return []

            tabs = result['data']['tabsInfo']['tabs']
            container_id = ''
            for tab in tabs:
                if tab['tabKey'] == 'weibo':
                    container_id = tab['containerid']

            # 获取正文列表
            r = await client.get(self.url + f'&containerid={container_id}', headers=self.headers)
            result = r.json()

            for item in result['data']['cards']:
                if item['card_type'] == 9 and 'isTop' not in item['mblog']:
                    cards.append(item)

        return cards


def remove_xml_tag(text: str):
    return re.compile(r'<[^>]+>', re.S).sub('', text)


class Game():
    def __init__(self):
        self.url = "https://ak-conf.hypergryph.com/config/prod/announce_meta/IOS/announcement.meta.json"

    async def get_announce(self):
        async with httpx.AsyncClient() as client:
            r = await client.get(self.url)
            result = r.json()

        return [x['webUrl'] for x in result['announceList']]

    async def get_screenshot(self, url):
        browser = await get_browser()
        page = None
        try:
            page = await browser.new_page()
            await page.goto(url, wait_until='networkidle', timeout=10000)
            await page.set_viewport_size({"width": 500, "height": 273})
            image = await page.screenshot(full_page=True, type='jpeg', quality=85)
            await page.close()
            return image
        except Exception:
            if page:
                await page.close()
            raise
