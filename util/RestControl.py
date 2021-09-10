from graia.saya import Channel
from graia.scheduler.timers import crontabify
from graia.application import GraiaMiraiApplication
from graia.broadcast.exceptions import ExecutionStop
from graia.broadcast.builtin.decorators import Depend
from graia.scheduler.saya.schema import SchedulerSchema
from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import Plain

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

def set_sleep(set):
    global SLEEP
    SLEEP = set

def rest_control():
    async def sleep():
        if SLEEP:
            raise ExecutionStop()
    return Depend(sleep)
