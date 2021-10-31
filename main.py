import os
import asyncio

from loguru import logger
from graia.saya import Saya
from graia.ariadne.app import Ariadne
from graia.broadcast import Broadcast
from graia.scheduler import GraiaScheduler
from graia.ariadne.model import MiraiSession
from graia.ariadne.adapter import DebugAdapter
from graia.ariadne.exception import AccountNotFound
from graia.broadcast.interrupt import InterruptControl
from graia.scheduler.saya import GraiaSchedulerBehaviour
from graia.saya.builtins.broadcast import BroadcastBehaviour

from config import yaml_data, save_config

ignore = ["__init__.py", "__pycache__"]

loop = asyncio.new_event_loop()
bcc = Broadcast(loop=loop)
scheduler = GraiaScheduler(loop, bcc)
inc = InterruptControl(bcc)

saya = Saya(bcc)
saya.install_behaviours(BroadcastBehaviour(bcc))
saya.install_behaviours(GraiaSchedulerBehaviour(scheduler))
saya.install_behaviours(InterruptControl(bcc))

app = Ariadne(
    broadcast=bcc,
    adapter=DebugAdapter(
        bcc,
        MiraiSession(
            host=yaml_data['Basic']['MAH']['MiraiHost'],
            account=yaml_data['Basic']['MAH']['BotQQ'],
            verify_key=yaml_data['Basic']['MAH']['MiraiAuthKey']
        )
    )
)

# with saya.module_context():
#     for module in os.listdir("saya"):
#         if module in ignore:
#             continue
#         if os.path.isdir(module):
#             saya.require(f"saya.{module}")
#         else:
#             saya.require(f"saya.{module.split('.')[0]}")
#     logger.info("saya加载完成")

with saya.module_context():
    saya.require("saya.AdminMSG")


async def main():
    await app.launch()
    await app.lifecycle()


def start():
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        loop.run_until_complete(app.stop())
        save_config()
    except AccountNotFound:
        loop.run_until_complete(app.stop())
        save_config()
        print("未能使用所配置的账号激活 sessionKey, 请检查 config.yaml 配置是否正确或检查 Mirai 是否正常登录该账号")


if __name__ == '__main__':
    start()
