import os

from typing import Optional
from playwright.async_api import Browser, async_playwright


path_to_extension = "./util/browser/extension/ad"
user_data_dir = "./util/browser/data"


_browser: Optional[Browser] = None


async def init() -> Browser:
    global _browser
    browser = await async_playwright().start()
    _browser = await browser.firefox.launch_persistent_context(
        user_data_dir,
        headless=True,
        args=[
            f"--disable-extensions-except={path_to_extension}",
            f"--load-extension={path_to_extension}",
        ],
        device_scale_factor=1.25,
    )
    return _browser


async def get_browser() -> Browser:
    return _browser or await init()


os.system("poetry run playwright install firefox")
