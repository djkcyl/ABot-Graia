import httpx
import random
import asyncio

from loguru import logger
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group
from graia.scheduler.timers import crontabify
from graia.ariadne.message.element import At, Plain
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import GroupMessage
from graia.scheduler.saya.schema import SchedulerSchema
from graia.saya.builtins.broadcast.schema import ListenerSchema

from config import yaml_data, group_data


saya = Saya.current()
channel = Channel.current()

print("正在下载词库")
root = httpx.get("https://raw.githubusercontents.com/Kyomotoi/AnimeThesaurus/main/data.json").json()


@channel.use(SchedulerSchema(crontabify("0 0 * * *")))
async def updateDict():
    global root
    await asyncio.sleep(1)
    logger.info(msg=f"已更新完成聊天词库，共计：{len(root)}条")


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def main(app: Ariadne, group: Group, message: MessageChain):

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
