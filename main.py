import asyncio
import os

from graia.application import GraiaMiraiApplication, Session
from graia.broadcast import Broadcast
from graia.saya import Saya
from graia.saya.builtins.broadcast import BroadcastBehaviour
from graia.scheduler import GraiaScheduler
from graia.scheduler.saya import GraiaSchedulerBehaviour
from graia.broadcast.interrupt import InterruptControl

from config import yaml_data

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
        # try:
        if os.path.isdir(module):
            saya.require(f"saya.{module}")
        else:
            saya.require(f"saya.{module.split('.')[0]}")
        # except ModuleNotFoundError:
        #     pass


try:
    app.launch_blocking()
except KeyboardInterrupt:
    pass
