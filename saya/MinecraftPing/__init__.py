from graia.saya import Channel
from graia.ariadne.model import Group
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    RegexResult,
    WildcardMatch,
)

from util.sendMessage import safeSendGroupMessage
from util.control import Function, Interval, Permission

from .mcping import mcping

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([FullMatch("/mcping"), "anything" @ WildcardMatch(optional=True)])
        ],
        decorators=[
            Function.require("MinecraftPing"),
            Permission.require(),
            Interval.require(),
        ],
    )
)
async def minecraft_ping(group: Group, anything: RegexResult):
    if anything.matched:
        send_msg = await mcping(anything.result.asDisplay())
        await safeSendGroupMessage(group, MessageChain.create(send_msg))
    else:
        await safeSendGroupMessage(group, MessageChain.create("用法：/mcping 服务器地址"))
