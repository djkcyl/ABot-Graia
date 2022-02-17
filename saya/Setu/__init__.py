import asyncio

from graia.saya import Saya, Channel
from graia.ariadne.model import Group
from graia.ariadne.message.element import Image
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import Twilight, FullMatch

from util.sendMessage import safeSendGroupMessage
from util.control import Permission, Interval, Rest, Function

from .setu import create_setu

saya = Saya.current()
channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight({"head": FullMatch("色图")})],
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
