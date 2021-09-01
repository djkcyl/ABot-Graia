import base64

from playwright.async_api import async_playwright


path_to_extension = "./saya/ChineseDict/chrome/extension/ad"
user_data_dir = "./saya/ChineseDict/chrome/data"

_browser = None

async def init():
    global _browser
    browser = await async_playwright().start()
    _browser = await browser.chromium.launch_persistent_context(
        user_data_dir,
        headless=True,
        args=[
            f"--disable-extensions-except={path_to_extension}",
            f"--load-extension={path_to_extension}",
        ],
    )

async def get_hans_screenshot(url):
    if _browser == None:
        await init()
    try:
        page = await _browser.new_page()
        await page.goto(url, wait_until='load', timeout=10000)
        await page.set_viewport_size({"width": 1600, "height": 2000})
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


def install():
    print("正在检查 Chromium 更新")
    import os
    os.system("poetry run playwright install chromium")


install()
