from graia.saya import Saya, Channel
from graia.application.event.mirai import *
from graia.application.event.messages import *
from graia.application import GraiaMiraiApplication
from graia.application.message.elements.internal import *
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.parser.literature import Literature

from config import yaml_data, sendmsg

from .beast import encode, decode


saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("嗷")]))
async def main(app: GraiaMiraiApplication, group: Group, message: MessageChain, source: Source):

    if yaml_data['Saya']['Beast']['Disabled']:
        return await sendmsg(app=app, group=group)
    elif group.id in yaml_data['Saya']['Beast']['Blacklist']:
        return await sendmsg(app=app, group=group)

    try:
        saying = message.asDisplay().split()
        msg = encode(saying[1])
        print(len(msg))
        if (len(msg)) < 2000:
            await app.sendGroupMessage(group, MessageChain.create([Plain(msg)]), quote=source.id)
        else:
            await app.sendGroupMessage(group, MessageChain.create([Plain(f"文字太长")]))
    except:
        await app.sendGroupMessage(group, MessageChain.create([Plain("明文错误``")]), quote=source.id)


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("呜")]))
async def main(app: GraiaMiraiApplication, group: Group, message: MessageChain, source: Source):

    if yaml_data['Saya']['Beast']['Disabled']:
        return await sendmsg(app=app, group=group)
    elif group.id in yaml_data['Saya']['Beast']['Blacklist']:
        return await sendmsg(app=app, group=group)

    try:
        saying = message.asDisplay().split()
        msg = decode(saying[1])
        await app.sendGroupMessage(group, MessageChain.create([Plain(msg)]), quote=source.id)
    except:
        await app.sendGroupMessage(group, MessageChain.create([Plain("密文错误``")]), quote=source.id)
