import re
import os

from graia.application import GraiaMiraiApplication
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.event.messages import *
from graia.application.event.mirai import *
from graia.application.message.elements.internal import *
from graia.application.message.parser.literature import Literature

from config import Config, sendmsg

from .mcping import mcping

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("/mcping")]))
async def minecraft_ping(app: GraiaMiraiApplication, group: Group, saying: MessageChain):
    
    if Config.Saya.MinecraftPing.Disabled:
        return await sendmsg(app=app, group=group)
    elif group.id in Config.Saya.MinecraftPing.Blacklist:
        return await sendmsg(app=app, group=group)
    
    pattern = re.compile('/mcping (.*)', re.M)
    try:
        say = pattern.search(saying.asDisplay()).group(1)
        send_msg = mcping(say)
        # print(send_msg)
        await app.sendGroupMessage(str(group.id), MessageChain.create(send_msg))
        try:
            os.remove("mcstatus_temp.jpg")
        except:
            return
    except:
        await app.sendGroupMessage(str(group.id), MessageChain.create([Plain("请输入服务器地址")]))
