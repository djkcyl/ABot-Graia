import requests
import asyncio

from io import BytesIO
from graia.application import GraiaMiraiApplication
from graia.saya import Saya, Channel
from graia.application.event.messages import *
from graia.application.event.mirai import *
from graia.scheduler.saya.schema import SchedulerSchema
from graia.scheduler.timers import crontabify
from graia.application.message.elements.internal import *


from config import yaml_data, group_data

saya = Saya.current()
channel = Channel.current()


@channel.use(SchedulerSchema(crontabify("* * 8 * * *")))
async def something_scheduled(app: GraiaMiraiApplication):

    if yaml_data['Saya']['DailyNewspaper']['Disabled']:
        return

    groupList = await app.groupList()
    paperurl = requests.get("http://api.2xb.cn/zaob").json()['imageUrl']
    paperimg = BytesIO()
    paperimg.write(requests.get(paperurl).content)

    for group in groupList:

        if 'DailyNewspaper' in group_data[group.id]['DisabledFunc']:
            return

        await app.sendGroupMessage(group.id, MessageChain.create([
            Plain(group.name),
            Image_UnsafeBytes(paperimg.getvalue())
        ]))
        await asyncio.sleep(1)
