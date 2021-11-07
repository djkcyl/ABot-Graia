import time
import httpx
import random
import asyncio

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Friend
from graia.scheduler.timers import crontabify
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import FriendMessage
from graia.ariadne.message.element import Plain, Image
from graia.scheduler.saya.schema import SchedulerSchema
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.literature import Literature

from util.control import Permission
from config import yaml_data, group_data

saya = Saya.current()
channel = Channel.current()


@channel.use(SchedulerSchema(crontabify("30 8 * * *")))
async def something_scheduled(app: Ariadne):
    if yaml_data['Saya']['DailyNewspaper']['Disabled']:
        return
    await send(app)


@channel.use(ListenerSchema(listening_events=[FriendMessage],
                            inline_dispatchers=[Literature("发送早报")],
                            decorators=[Permission.require(Permission.MASTER)]))
async def main(app: Ariadne, friend: Friend):
    await send(app)


async def send(app: Ariadne):
    ts = time.time()
    groupList = await app.getGroupList()
    groupNum = len(groupList)
    await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
        Plain(f"正在开始发送每日日报，当前共有 {groupNum} 个群")
    ]))
    for i in range(3):
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get("http://api.2xb.cn/zaob")
                paperurl = r.json()['imageUrl']
                r2 = await client.get(paperurl)
                paperimg = r2.content
            break
        except Exception as err:
            await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
                Plain(f"第 {i + 1} 次日报加载失败\n{err}")
            ]))
            await asyncio.sleep(3)
    else:
        return await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
            Plain("日报加载失败，请稍后手动重试")
        ]))
    await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
        Image(data_bytes=paperimg)
    ]))
    for group in groupList:

        if 'DailyNewspaper' in group_data[str(group.id)]['DisabledFunc']:
            continue
        try:
            await app.sendGroupMessage(group.id, MessageChain.create([
                Plain(group.name),
                Image(data_bytes=paperimg)
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
