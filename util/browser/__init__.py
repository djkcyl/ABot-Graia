import os
import sys

from loguru import logger
from typing import Optional
from playwright.__main__ import main
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


def install():
    """自动安装、更新 Chromium"""

    def restore_env():
        del os.environ["PLAYWRIGHT_DOWNLOAD_HOST"]

    logger.info("检查 Chromium 更新")
    sys.argv = ["", "install", "chromium"]
    os.environ["PLAYWRIGHT_DOWNLOAD_HOST"] = "https://playwright.sk415.workers.dev"
    success = False
    try:
        main()
    except SystemExit as e:
        if e.code == 0:
            success = True
    if not success:
        logger.info("Chromium 更新失败，尝试从原始仓库下载，速度较慢")
        os.environ["PLAYWRIGHT_DOWNLOAD_HOST"] = ""
        try:
            main()
        except SystemExit as e:
            if e.code != 0:
                restore_env()
                raise RuntimeError("未知错误，Chromium 下载失败")
    restore_env()


install()
