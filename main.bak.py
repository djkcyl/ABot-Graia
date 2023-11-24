import os

from creart import it
from pathlib import Path
from graia.saya import Saya
from graia.ariadne.app import Ariadne
from graia.scheduler import GraiaScheduler
from graiax.playwright.service import PlaywrightService
from graia.amnesia.builtins.memcache import MemcacheService
from graia.ariadne.entry import config, HttpClientConfig, WebsocketClientConfig

from core_bak.logger import logger
from core_bak.s3file import WeedFSService
from core_bak.data_file import get_data_path

os.environ["PLAYWRIGHT_BROWSERS_PATH"] = get_data_path("browser", "bin").as_posix()

logger.info("ABot is starting...")


host = "http://127.0.0.1:8066"
app_config = config(
    123456789,
    "token",
    HttpClientConfig(host),
    WebsocketClientConfig(host),
)
app = Ariadne(app_config)
app.config(install_log=True, inject_bypass_listener=True)
app.launch_manager.add_service(
    PlaywrightService(
        # user_data_dir=get_data_path("browser", "data"),
        # device_scale_factor=1.25,
        # user_agent=(
        #     "Mozilla/5.0 (Linux; Android 10; RMX1911) AppleWebKit/537.36 "
        #     "(KHTML, like Gecko) Chrome/100.0.4896.127 Mobile Safari/537.36"
        # ),
    )
)
app.launch_manager.add_service(MemcacheService())
app.launch_manager.add_service(WeedFSService())
app.create(GraiaScheduler)

saya = it(Saya)

with saya.module_context():
    ignore = ["__init__.py", "__pycache__"]
    for module in Path("func").glob("**/__init__.py"):
        if module in ignore:
            continue
        module_name = ".".join(module.parent.parts)
        saya.require(module_name)
    logger.info("Saya 加载完成")


if __name__ == "__main__":
    app.launch_blocking()
