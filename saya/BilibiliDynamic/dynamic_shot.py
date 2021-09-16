from util.browser import get_browser


async def get_dynamic_screenshot(id):
    url = f"https://t.bilibili.com/{id}"
    browser = await get_browser()
    page = None
    try:
        page = await browser.new_page()
        await page.goto(url, wait_until='networkidle', timeout=10000)
        await page.set_viewport_size({"width": 2560, "height": 1080})
        card = await page.query_selector(".card")
        assert card is not None
        clip = await card.bounding_box()
        assert clip is not None
        bar = await page.query_selector(".text-bar")
        assert bar is not None
        bar_bound = await bar.bounding_box()
        assert bar_bound is not None
        clip['height'] = bar_bound['y'] - clip['y']
        image = await page.screenshot(clip=clip)
        await page.close()
        return image
    except Exception:
        if page:
            await page.close()
        raise
