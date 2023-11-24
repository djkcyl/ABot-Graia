from graia.saya import Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group
from graia.ariadne.event.lifecycle import ApplicationLaunched
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.parser.twilight import Twilight, FullMatch

from core.model import AUserModel, FuncType
from core.function import build_metadata


channel = Channel.current()
channel.meta = build_metadata(
    func_type=FuncType.tool,
    name="Hello World",
    version="1.0",
    description="Hello World",
    usage=["发送指令：/hello"],
)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(FullMatch("/hello"))],
    )
)
async def main(app: Ariadne, event: GroupMessage, group: Group):
    await app.send_group_message(group, str(event.dict()))
