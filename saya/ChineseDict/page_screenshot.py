import base64

from typing import Optional
from playwright.async_api import Browser, async_playwright


_browser: Optional[Browser] = None

async def init(**kwargs) -> Browser:
    args = []
    
    global _browser
    browser = await async_playwright().start()
    _browser = await browser.chromium.launch(args=args, **kwargs)
    return _browser


async def get_browser(**kwargs) -> Browser:
    return _browser or await init(**kwargs)


async def get_hans_screenshot(url):
    browser = await get_browser()
    page = None
    try:
        page = await browser.new_page()
        await page.goto(url, wait_until='load', timeout=10000)
        await page.set_viewport_size({"width": 1300, "height": 6880})
        card = await page.query_selector(".shiyi_content")
        # await page.evaluate()
        assert card is not None
        image = await card.screenshot(type='jpeg', quality=90)
        await page.close()
        return base64.b64encode(image).decode()
    except Exception:
        if page:
            await page.close()
        raise