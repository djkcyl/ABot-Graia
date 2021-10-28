import httpx
import random
import asyncio

from graia.saya import Saya, Channel
from graia.application.group import Group
from graia.application.friend import Friend
from graia.scheduler.timers import crontabify
from graia.application import GraiaMiraiApplication
from graia.scheduler.saya.schema import SchedulerSchema
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.event.messages import GroupMessage, FriendMessage
from graia.application.message.elements.internal import MessageChain, At, Plain

from config import yaml_data, group_data


saya = Saya.current()
channel = Channel.current()

print("正在下载词库")
root = httpx.get("https://raw.githubusercontents.com/Kyomotoi/AnimeThesaurus/main/data.json").json()


@channel.use(SchedulerSchema(crontabify("0 0 * * *")))
async def updateDict(app: GraiaMiraiApplication):
    global root
    await asyncio.sleep(1)
    app.logger.info(msg=f"已更新完成聊天词库，共计：{len(root)}条")


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def main(app: GraiaMiraiApplication, group: Group, message: MessageChain):

    if yaml_data['Saya']['ChatMS']['Disabled']:
        return
    elif 'ChatMS' in group_data[group.id]['DisabledFunc']:
        return

    if message.has(At):
        if message.getFirst(At).target == yaml_data['Basic']['MAH']['BotQQ']:
            saying = message.getFirst(Plain).text
            for key in root:
                if key in saying:
                    return await app.sendGroupMessage(group, MessageChain.create([
                        Plain(random.choice(root[key]))
                    ]))


@channel.use(ListenerSchema(listening_events=[FriendMessage]))
async def main(app: GraiaMiraiApplication, friend: Friend, message: MessageChain):

    if yaml_data['Saya']['ChatMS']['Disabled']:
        return

    saying = message.getFirst(Plain).text
    for key in root:
        if key in saying:
            return await app.sendFriendMessage(friend, MessageChain.create([
                Plain(random.choice(root[key]))
            ]))
