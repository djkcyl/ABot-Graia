from pathlib import Path

from graia.saya import Channel
from graia.ariadne.model import Group
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Plain
from graia.saya.builtins.broadcast.schema import ListenerSchema

from util.sendMessage import safeSendGroupMessage
from util.control import Function, Interval, Permission

channel = Channel.current()

HOME = Path(__file__).parent


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        decorators=[
            Function.require("Message"),
            Permission.require(),
        ],
    )
)
async def az(group: Group, message: MessageChain):
    saying = message.asDisplay()
    if saying == "草":
        await Interval.manual(5)
        await safeSendGroupMessage(group, MessageChain.create([Plain("一种植物（")]))
    if saying == "好耶":
        await Interval.manual(5)
        await safeSendGroupMessage(
            group, MessageChain.create([Image(path=HOME.joinpath("haoye.png"))])
        )
    if saying == "流汗黄豆.jpg":
        await Interval.manual(5)
        await safeSendGroupMessage(
            group, MessageChain.create([Image(path=HOME.joinpath("huangtou.jpg"))])
        )
