import asyncio

from graia.saya import Channel
from graia.ariadne.model import Group
from graia.ariadne.message.element import Image
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import FullMatch, Twilight

from util.sendMessage import safeSendGroupMessage
from core_bak.control import Function, Interval, Permission, Rest

from .setu import create_setu

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("色图")])],
        decorators=[
            Function.require("Setu"),
            Permission.require(),
            Rest.rest_control(),
            Interval.require(),
        ],
    )
)
async def main(group: Group):
    await safeSendGroupMessage(
        group,
        MessageChain.create([Image(data_bytes=await asyncio.to_thread(create_setu))]),
    )
