import contextlib
import os
import asyncio

from pathlib import Path
from loguru import logger
from graia.saya import Saya
from graia.ariadne.app import Ariadne
from graia.broadcast import Broadcast
from graia.scheduler import GraiaScheduler
from graia.ariadne.model import MiraiSession
from graia.ariadne.adapter import DefaultAdapter
from graia.broadcast.interrupt import InterruptControl
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


saya = Saya(bcc)
saya.install_behaviours(BroadcastBehaviour(bcc))
saya.install_behaviours(GraiaSchedulerBehaviour(scheduler))

with saya.module_context():
    for module in os.listdir("saya"):
        if module in ignore:
            continue
        module_name = module if os.path.isdir(module) else module.split(".")[0]
        with contextlib.suppress(KeyError):
            if yaml_data["Saya"][module_name]["Disabled"]:
                continue
        saya.require(f"saya.{module_name}")
    logger.info("saya加载完成")


if __name__ == "__main__":
    app.launch_blocking()
