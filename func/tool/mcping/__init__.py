from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group
from graia.ariadne.event.message import GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    RegexResult,
    WildcardMatch,
)

from core.model import FuncType
from core.preprocessor import MentionMe
from core.function import build_metadata
from core.control import Permission, Interval, Function

from .mcping import get_mcping
from .crud import get_bind, set_bind, delete_bind

channel = Channel.current()
channel.meta = build_metadata(
    func_type=FuncType.tool,
    name="Minecraft服务器状态查询",
    version="1.0",
    description="查询Minecraft服务器状态",
    usage=[
        "发送指令：mcping [bind] <address>",
    ],
    options=[
        {"name": "bind", "help": "绑定服务器"},
        {"name": "address", "help": "服务器地址，可选"},
    ],
    example=[
        {"run": "mcping bind a60.one", "to": "在本群绑定服务器 a60.one"},
        {"run": "mcping a60.one", "to": "查询服务器 a60.one 的状态"},
        {"run": "mcping", "to": "查询本群绑定的服务器状态"},
    ],
)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    FullMatch("mcping"),
                    "arg_bind" @ FullMatch("bind", optional=True),
                    "arg_address" @ WildcardMatch(optional=True),
                ],
                preprocessor=MentionMe(),
            )
        ],
        decorators=[
            Function.require(),
            Permission.require(),
            Interval.require(),
        ],
    )
)
async def main(
    app: Ariadne,
    group: Group,
    arg_bind: RegexResult,
    arg_address: RegexResult,
):
    address = await get_bind(group.id)
    address = (
        address.address if address else arg_address.result.display if arg_address.result else ""
    )
    if arg_bind.result and not arg_address.result and address:
        await delete_bind(group.id)
        await app.send_group_message(group, f"服务器 {address} 解绑成功")
    elif arg_bind.result and not arg_address.result or not arg_bind.result and not address:
        await app.send_group_message(group, "本群未绑定服务器")
    elif arg_bind.result:
        await set_bind(group.id, address)
        await app.send_group_message(group, f"服务器 {address} 绑定成功")
    else:
        ping_result = await get_mcping(address)
        await app.send_group_message(group, ping_result)
