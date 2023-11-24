import httpx

from graia.saya import Channel
from graia.ariadne.model import Group
from graia.ariadne.message.element import Image
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import Twilight, RegexMatch

from util.sendMessage import safeSendGroupMessage
from core.control import Function, Interval, Permission


channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch(r"^(一眼|来[点张])[顶丁钉][真针]|[Dd]ing[！!]?$")])],
        decorators=[
            Function.require("DingZhen"),
            Permission.require(),
            Interval.require(30),
        ],
    )
)
async def ding(group: Group):
    async with httpx.AsyncClient() as client:
        resp = await client.get("https://api.aya1.top/randomdj?r=0")
        await safeSendGroupMessage(
            group, MessageChain.create([Image(url=resp.json()["url"])])
        )
