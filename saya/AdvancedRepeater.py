from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group, Member
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.mirai import GroupRecallEvent
from graia.ariadne.message.parser.twilight import Twilight
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.element import At, Quote, Source
from graia.ariadne.message.parser.pattern import ElementMatch, FullMatch, RegexMatch

from util.control import Permission
from util.sendMessage import safeSendGroupMessage


saya = Saya.current()
channel = Channel.current()


REPEATER = {"statu": False, "group": None, "member": None}

MESSAGEID = {"origin": [], "bot": []}


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                {
                    "head": FullMatch("/rep"),
                    "operate": RegexMatch(r"on|off", optional=True),
                    "at": ElementMatch(At, optional=True),
                }
            )
        ],
        decorators=[Permission.require(Permission.MASTER)],
    )
)
async def main(group: Group, operate: RegexMatch, at: ElementMatch):

    global REPEATER

    if operate.matched:
        operate = operate.result.asDisplay()
        if operate == "on":
            if at.matched:
                if REPEATER["statu"]:
                    repid = REPEATER["member"].id
                    await safeSendGroupMessage(
                        group, MessageChain.create(f"复读机当前为开启状态\n正在复读的用户：{repid}")
                    )
                else:
                    REPEATER["statu"] = True
                    REPEATER["group"] = group.id
                    REPEATER["member"] = at.result.target
                    await safeSendGroupMessage(group, MessageChain.create("复读机开始工作"))
            else:
                await safeSendGroupMessage(group, MessageChain.create("请@需要复读的人"))
        elif operate == "off":
            if REPEATER["statu"]:
                REPEATER["statu"] = False
                REPEATER["group"] = None
                REPEATER["member"] = None
                await safeSendGroupMessage(group, MessageChain.create("复读机已关闭"))
            else:
                await safeSendGroupMessage(group, MessageChain.create("复读机当前未开启"))

        else:
            await safeSendGroupMessage(group, MessageChain.create("操作仅可为 on 或 off"))
    else:
        await safeSendGroupMessage(group, MessageChain.create("请输入要进行的操作"))


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def rep(group: Group, member: Member, message: MessageChain, source: Source):

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
