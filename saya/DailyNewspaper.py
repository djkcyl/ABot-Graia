import requests
import asyncio
import random
import time

from io import BytesIO
from graia.saya import Saya, Channel
from graia.application.friend import Friend
from graia.scheduler.timers import crontabify
from graia.application import GraiaMiraiApplication
from graia.scheduler.saya.schema import SchedulerSchema
from graia.application.event.messages import FriendMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.parser.literature import Literature
from graia.application.message.elements.internal import MessageChain, Plain, Image_UnsafeBytes

from config import yaml_data, group_data
from util.aiorequests import aiorequests

saya = Saya.current()
channel = Channel.current()


@channel.use(SchedulerSchema(crontabify("30 8 * * *")))
async def something_scheduled(app: GraiaMiraiApplication):
    if yaml_data['Saya']['DailyNewspaper']['Disabled']:
        return
    await send(app=app)


@channel.use(ListenerSchema(listening_events=[FriendMessage], inline_dispatchers=[Literature("发送早报")]))
async def main(app: GraiaMiraiApplication, friend: Friend):
    if friend.id == yaml_data['Basic']['Permission']['Master']:
        await send(app=app)


async def send(app):
    ts = time.time()
    groupList = await app.groupList()
    groupNum = len(groupList)
    await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
        Plain(f"正在开始发送每日日报，当前共有 {groupNum} 个群")
    ]))
    for i in range(3):
        try:
            paperurl = await aiorequests.get("http://api.2xb.cn/zaob")
            paperurl = await paperurl.json()
            paperurl = paperurl['imageUrl']
            paperimg = await aiorequests.get(paperurl)
            paperimg = await paperimg.content
            paperimgbio = BytesIO()
            paperimgbio.write(paperimg) 
            break
        except Exception as err:
            await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
                Plain(f"第 {i + 1} 次日报加载失败\n{err}")
            ]))
            await asyncio.sleep(3)
    await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
        Image_UnsafeBytes(paperimgbio.getvalue())
    ]))
    for group in groupList:

        if 'DailyNewspaper' in group_data[group.id]['DisabledFunc']:
            continue
        try:
            await app.sendGroupMessage(group.id, MessageChain.create([
                Plain(group.name),
                Image_UnsafeBytes(paperimgbio.getvalue())
            ]))
        except Exception as err:
            await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
                Plain(f"{group.id} 的日报发送失败\n{err}")
            ]))
        await asyncio.sleep(random.randint(3, 6))
    allTime = time.time() - ts
    await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
        Plain(f"每日日报已发送完毕，共用时 {str(int(allTime))} 秒")
    ]))
