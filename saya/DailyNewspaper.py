import requests
import asyncio
import random
import time

from io import BytesIO
from graia.saya import Saya, Channel
from graia.scheduler.timers import crontabify
from graia.application import GraiaMiraiApplication, message
from graia.scheduler.saya.schema import SchedulerSchema
from graia.application.exceptions import AccountMuted
from graia.application.message.elements.internal import MessageChain, Plain, Image_UnsafeBytes

from config import yaml_data, group_data

saya = Saya.current()
channel = Channel.current()


@channel.use(SchedulerSchema(crontabify("0 8 * * *")))
async def something_scheduled(app: GraiaMiraiApplication):

    if yaml_data['Saya']['DailyNewspaper']['Disabled']:
        return

    ts = time.time()

    groupList = await app.groupList()
    groupNum = len(groupList)
    paperurl = requests.get("http://api.2xb.cn/zaob").json()['imageUrl']
    paperimg = BytesIO()
    paperimg.write(requests.get(paperurl).content)
    await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
        Plain(f"正在开始发送每日日报，当前共有 {groupNum} 个群")
    ]))
    for group in groupList:

        if 'DailyNewspaper' in group_data[group.id]['DisabledFunc']:
            continue
        try:
            await app.sendGroupMessage(group.id, MessageChain.create([
                Plain(group.name),
                Image_UnsafeBytes(paperimg.getvalue())
            ]))
        except Exception as err:
            await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
                Plain(f"{group.id} 的日报发送失败\n{err}")
            ]))
        await asyncio.sleep(random.randint(1, 4))
    allTime = time.time() - ts
    await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
        Plain(f"每日日报已发送完毕，共用时 {str(allTime)} 秒")
    ]))
