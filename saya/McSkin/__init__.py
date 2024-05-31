from graia.saya import Channel
from graia.ariadne.model import Group
from graia.ariadne.message.element import Image
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
from util.control import Interval, Permission

from .mcskin import MinecraftSkin

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([FullMatch("/mcskin"), "anything" @ WildcardMatch(optional=True)])
        ],
        decorators=[
            Permission.require(),
            Interval.require(),
        ],
    )
)
async def minecraft_skin(group: Group, anything: RegexResult):
    skin = MinecraftSkin(anything.result.asDisplay())
    await safeSendGroupMessage(
        group, MessageChain.create(Image(data_bytes=await skin.get_body_rander()))
    )
