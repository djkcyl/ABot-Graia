from graia.saya import Saya, Channel
from graia.application.group import Group, Member
from graia.application import GraiaMiraiApplication
from graia.broadcast.interrupt.waiter import Waiter
from graia.broadcast.interrupt import InterruptControl
from graia.application.event.messages import GroupMessage
from graia.application.event.mirai import GroupRecallEvent
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.parser.literature import Literature
from graia.application.message.elements.internal import At, MessageChain, Plain, Image, FlashImage, Quote, Source, Xml, Json, Voice

from util.limit import manual_limit
from config import yaml_data, group_data
from util.TextModeration import text_moderation
from util.ImageModeration import image_moderation


saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
inc = InterruptControl(bcc)


REPEATER = {
    "statu": False,
    "group": None,
    "member": None
}

MESSAGEID = {
    "origin": [],
    "bot": []
}


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Literature("/rep")]))
async def main(app: GraiaMiraiApplication, group: Group, member: Member, message: MessageChain):

    global REPEATER

    if member.id == yaml_data['Basic']['Permission']['Master']:
        if message.asDisplay().split()[1] == "on":
            if REPEATER["statu"]:
                repid = REPEATER["member"].id
                return await app.sendGroupMessage(group, MessageChain.create([
                    Plain(f"复读机当前为开启状态\n正在复读的用户：{repid}")
                ]))
            else:
                REPEATER["statu"] = True
                REPEATER["group"] = group.id
                REPEATER["member"] = message.getFirst(At).target
                return await app.sendGroupMessage(group, MessageChain.create([
                    Plain(f"复读机开始工作")
                ]))
        elif message.asDisplay().split()[1] == "off":
            if REPEATER["statu"]:
                REPEATER["statu"] = False
                REPEATER["group"] = None
                REPEATER["member"] = None
                return await app.sendGroupMessage(group, MessageChain.create([
                    Plain(f"复读机已关闭")
                ]))
            else:
                return await app.sendGroupMessage(group, MessageChain.create([
                    Plain(f"复读机当前未开启")
                ]))


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def rep(app: GraiaMiraiApplication, group: Group, member: Member, message: MessageChain, source: Source):

    if REPEATER["statu"] and REPEATER["group"] == group.id and REPEATER["member"] == member.id:
        quote_id = message.getFirst(Quote).id if message.has(Quote) else None
        masid = await app.sendGroupMessage(group, message.asSendable(), quote=quote_id)
        MESSAGEID["bot"].append(masid.messageId)
        MESSAGEID["origin"].append(source.id)


@channel.use(ListenerSchema(listening_events=[GroupRecallEvent]))
async def rep(app: GraiaMiraiApplication, event: GroupRecallEvent):

    if REPEATER["statu"] and REPEATER["group"] == event.group.id:
        if event.messageId in MESSAGEID["origin"]:
            index = MESSAGEID["origin"].index(event.messageId)
            await app.revokeMessage(MESSAGEID["bot"][index])
