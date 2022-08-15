import os
import time
import httpx
import asyncio

from pathlib import Path
from loguru import logger
from graia.saya import Saya
from graia.ariadne.app import Ariadne
from graia.broadcast import Broadcast
from prompt_toolkit.styles import Style
from graia.ariadne.console import Console
from graia.scheduler import GraiaScheduler
from graia.ariadne.model import MiraiSession
from prompt_toolkit.formatted_text import HTML
from graia.ariadne.adapter import DefaultAdapter
from graia.broadcast.interrupt import InterruptControl
from graia.ariadne.console.saya import ConsoleBehaviour
from graia.scheduler.saya import GraiaSchedulerBehaviour
from graia.saya.builtins.broadcast import BroadcastBehaviour

from config import yaml_data, save_config

LOGPATH = Path("./logs")
LOGPATH.mkdir(exist_ok=True)
logger.add(
    LOGPATH.joinpath("latest.log"),
    encoding="utf-8",
    backtrace=True,
    diagnose=True,
    rotation="00:00",
    retention="3 years",
    compression="tar.xz",
    colorize=False,
)
logger.info("ABot is starting...")

ignore = ["__init__.py", "__pycache__"]

loop = asyncio.new_event_loop()
bcc = Broadcast(loop=loop)
scheduler = GraiaScheduler(loop, bcc)
inc = InterruptControl(bcc)
app = Ariadne(
    broadcast=bcc,
    connect_info=DefaultAdapter(
        bcc,
        MiraiSession(
            host=yaml_data["Basic"]["MAH"]["MiraiHost"],
            account=yaml_data["Basic"]["MAH"]["BotQQ"],
            verify_key=yaml_data["Basic"]["MAH"]["MiraiAuthKey"],
        ),
    ),
)
console = Console(
    broadcast=bcc,
    prompt=HTML("<abot> ABot </abot>> "),
    style=Style(
        [
            ("abot", "fg:#ffffff"),
        ]
    ),
)


saya = Saya(bcc)
saya.install_behaviours(BroadcastBehaviour(bcc))
saya.install_behaviours(GraiaSchedulerBehaviour(scheduler))
saya.install_behaviours(ConsoleBehaviour(console))

with saya.module_context():
    for module in os.listdir("saya"):
        if module in ignore:
            continue
        module_name = module if os.path.isdir(module) else module.split('.')[0]
        try:
            if yaml_data['Saya'][module_name]['Disabled']:
                continue
        except KeyError:
            pass
        saya.require(f"saya.{module_name}")
    logger.info("saya加载完成")


if __name__ == "__main__":
    logger.info("正在检测 MAH 是否启动")
    while True:
        try:
            mah = httpx.get(yaml_data["Basic"]["MAH"]["MiraiHost"] + "/about")
            if mah.status_code == 200:
                app.launch_blocking()
                save_config()
                break
            else:
                time.sleep(3)
                logger.critical("MAH 尚未启动，正在重试...")
        except httpx.HTTPError:
            logger.critical("MAH 尚未启动，请检查")
            break
        except KeyboardInterrupt:
            break
