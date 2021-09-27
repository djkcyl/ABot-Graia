import time

from graia.saya import Channel
from graia.scheduler.timers import crontabify
from graia.application import GraiaMiraiApplication
from graia.broadcast.exceptions import ExecutionStop
from graia.broadcast.builtin.decorators import Depend
from graia.scheduler.saya.schema import SchedulerSchema
from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import Plain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.event.lifecycle import ApplicationLaunched

from config import yaml_data


channel = Channel.current()


SLEEP = 0

@channel.use(SchedulerSchema(crontabify("30 7 * * *")))
async def something_scheduled(app: GraiaMiraiApplication):
    set_sleep(0)
    await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
        Plain("已退出休息时间")
    ]))

@channel.use(SchedulerSchema(crontabify("0 0 * * *")))
async def something_scheduled(app: GraiaMiraiApplication):
    set_sleep(1)
    await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
        Plain("已进入休息时间")
    ]))

@channel.use(ListenerSchema(listening_events=[ApplicationLaunched]))
async def groupDataInit(app: GraiaMiraiApplication):
    now_localtime = time.strftime("%H:%M:%S", time.localtime())
    if "00:00:00" < now_localtime < "07:30:00":
        set_sleep(1)
        await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
            Plain("当前为休息时间，已进入休息状态")
        ]))


def set_sleep(set):
    global SLEEP
    SLEEP = set

def rest_control():
    async def sleep():
        if SLEEP:
            raise ExecutionStop()
    return Depend(sleep)


