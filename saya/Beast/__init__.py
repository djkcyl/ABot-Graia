from graia.saya import Saya, Channel
from graia.application import GraiaMiraiApplication
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.event.messages import GroupMessage, Group
from graia.application.message.parser.literature import Literature
from graia.application.message.elements.internal import MessageChain, Source, Plain

from util.RestControl import rest_control
from util.limit import member_limit_check
from util.TextModeration import text_moderation
from config import yaml_data, group_data, sendmsg

from .beast import encode, decode


saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Literature("嗷")],
                            headless_decorators=[rest_control(), member_limit_check(15)]))
async def main(app: GraiaMiraiApplication, group: Group, message: MessageChain, source: Source):

    if yaml_data['Saya']['Beast']['Disabled']:
        return await sendmsg(app=app, group=group)
    elif 'Beast' in group_data[group.id]['DisabledFunc']:
        return await sendmsg(app=app, group=group)

    try:
        saying = message.asDisplay().split(" ", 1)
        msg = encode(saying[1])
        if (len(msg)) < 500:
            await app.sendGroupMessage(group, MessageChain.create([Plain(msg)]), quote=source.id)
        else:
            await app.sendGroupMessage(group, MessageChain.create([Plain(f"文字过长")]), quote=source.id)
    except:
        await app.sendGroupMessage(group, MessageChain.create([Plain("明文错误``")]), quote=source.id)


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Literature("呜")],
                            headless_decorators=[rest_control(), member_limit_check(15)]))
async def main(app: GraiaMiraiApplication, group: Group, message: MessageChain, source: Source):

    if yaml_data['Saya']['Beast']['Disabled']:
        return await sendmsg(app=app, group=group)
    elif 'Beast' in group_data[group.id]['DisabledFunc']:
        return await sendmsg(app=app, group=group)

    try:
        saying = message.asDisplay().split(" ", 1)
        msg = decode(saying[1])
        res = await text_moderation(msg)
        if res['Suggestion'] == "Pass":
            await app.sendGroupMessage(group, MessageChain.create([Plain(msg)]), quote=source.id)
    except:
        await app.sendGroupMessage(group, MessageChain.create([Plain("密文错误``")]), quote=source.id)
