import asyncio
import os

from graia.application import GraiaMiraiApplication, Session
from graia.application.exceptions import AccountNotFound
from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import Plain
from graia.broadcast import Broadcast
from graia.broadcast.interrupt import InterruptControl
from graia.saya import Saya
from graia.saya.builtins.broadcast import BroadcastBehaviour
from graia.scheduler import GraiaScheduler
from graia.scheduler.saya import GraiaSchedulerBehaviour

from config import yaml_data, save_config

ignore = ["__init__.py", "__pycache__"]

loop = asyncio.get_event_loop()
bcc = Broadcast(loop=loop)
scheduler = GraiaScheduler(loop, bcc)
inc = InterruptControl(bcc)

saya = Saya(bcc)
saya.install_behaviours(BroadcastBehaviour(bcc))
saya.install_behaviours(GraiaSchedulerBehaviour(scheduler))
saya.install_behaviours(InterruptControl(bcc))

app = GraiaMiraiApplication(
    broadcast=bcc,
    connect_info=Session(
        host=yaml_data['Basic']['MAH']['MiraiHost'],
        authKey=yaml_data['Basic']['MAH']['MiraiAuthKey'],
        account=yaml_data['Basic']['MAH']['BotQQ'],
        websocket=True
    )
)

with saya.module_context():
    for module in os.listdir("saya"):
        if module in ignore:
            continue
        if os.path.isdir(module):
            saya.require(f"saya.{module}")
        else:
            saya.require(f"saya.{module.split('.')[0]}")

try:
    app.launch_blocking()
except KeyboardInterrupt:
    save_config()
except AccountNotFound:
    save_config()
    print("未能使用所配置的账号激活 sessionKey, 请检查 config.yaml 配置是否正确或检查 Mirai 是否正常登录该账号")
