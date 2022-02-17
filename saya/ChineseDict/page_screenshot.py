from util.browser import get_browser


async def get_hans_screenshot(url):
    _browser = await get_browser()
    page = None
    try:
        page = await _browser.new_page()
        await page.goto(url, wait_until="load", timeout=10000)
        await page.set_viewport_size({"width": 1600, "height": 2000})
        card = await page.query_selector(".shiyi_content")
        # await page.evaluate()
        assert card is not None
        image = await card.screenshot(type="jpeg", quality=90)
        await page.close()
        return image
    except Exception:
        if page:
            await page.close()
        raise
