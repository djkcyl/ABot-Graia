from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group, Member
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.mirai import GroupRecallEvent
from graia.ariadne.message.parser.literature import Literature
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.element import At, Plain, Quote, Source

from util.control import Permission
from util.sendMessage import safeSendGroupMessage


saya = Saya.current()
channel = Channel.current()


REPEATER = {"statu": False, "group": None, "member": None}

MESSAGEID = {"origin": [], "bot": []}


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Literature("/rep")],
        decorators=[Permission.require(Permission.MASTER)],
    )
)
async def main(app: Ariadne, group: Group, message: MessageChain):

    global REPEATER

    if message.asDisplay().split()[1] == "on":
        if REPEATER["statu"]:
            repid = REPEATER["member"].id
            return await safeSendGroupMessage(
                group, MessageChain.create([Plain(f"复读机当前为开启状态\n正在复读的用户：{repid}")])
            )
        else:
            REPEATER["statu"] = True
            REPEATER["group"] = group.id
            REPEATER["member"] = message.getFirst(At).target
            return await safeSendGroupMessage(
                group, MessageChain.create([Plain("复读机开始工作")])
            )
    elif message.asDisplay().split()[1] == "off":
        if REPEATER["statu"]:
            REPEATER["statu"] = False
            REPEATER["group"] = None
            REPEATER["member"] = None
            return await safeSendGroupMessage(
                group, MessageChain.create([Plain("复读机已关闭")])
            )
        else:
            return await safeSendGroupMessage(
                group, MessageChain.create([Plain("复读机当前未开启")])
            )


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def rep(
    app: Ariadne, group: Group, member: Member, message: MessageChain, source: Source
):

    if (
        REPEATER["statu"]
        and REPEATER["group"] == group.id
        and REPEATER["member"] == member.id
    ):
        quote_id = message.getFirst(Quote).id if message.has(Quote) else None
        masid = await safeSendGroupMessage(group, message.asSendable(), quote=quote_id)
        MESSAGEID["bot"].append(masid.messageId)
        MESSAGEID["origin"].append(source.id)


@channel.use(ListenerSchema(listening_events=[GroupRecallEvent]))
async def rep_recal(app: Ariadne, event: GroupRecallEvent):

    if REPEATER["statu"] and REPEATER["group"] == event.group.id:
        if event.messageId in MESSAGEID["origin"]:
            index = MESSAGEID["origin"].index(event.messageId)
            await app.revokeMessage(MESSAGEID["bot"][index])
