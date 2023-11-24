from typing import Annotated
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group, Member
from graia.ariadne.message.element import At, Source
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    ArgResult,
    ResultValue,
    ElementMatch,
    ElementResult,
    WildcardMatch,
    ArgumentMatch,
)

from core.preprocessor import MentionMe
from core.function import build_metadata
from core.model import AUserModel, FuncType
from core.control import Permission, Interval, Function


channel = Channel.current()
channel.meta = build_metadata(
    func_type=FuncType.user,
    name="转账",
    version="1.0",
    description="转账给其他人",
    usage=["发送指令：转账 <At> <数量> [-a, --all]"],
    options=[
        {"name": "At", "help": "要转账的对象，请使用群内的 At 功能，必选"},
        {"name": "数量", "help": "要转账的数量，和 --all 二选一，必选"},
        {"name": "-a, --all", "help": "是否转账所有可用的数量，和 数量 二选一，可选"},
    ],
    example=[
        {"run": "转账 @xxx 1", "to": "转账1个游戏币给 xxx"},
        {"run": "转账 @xxx --all", "to": "转账所有可用的游戏币给 xxx"},
    ],
    can_be_disabled=False,
)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    FullMatch("转账"),
                    "arg_at" @ ElementMatch(At, optional=True),
                    "arg_all" @ ArgumentMatch("-a", "--all", action="store_true"),
                    "arg_num" @ WildcardMatch(),
                ],
                preprocessor=MentionMe(),
            ),
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
    member: Member,
    arg_at: ElementResult,
    arg_all: ArgResult,
    arg_num: Annotated[MessageChain, ResultValue()],
    source: Source,
    auser: AUserModel,
):
    if not arg_at.result:
        return await app.send_group_message(group, "未 At 指定要转账的对象", quote=source)

    at_result: At = arg_at.result  # type: ignore
    if at_result.target == member.id:
        return await app.send_group_message(group, "不能转账给自己", quote=source)

    if arg_all.result:
        num = auser.coin
    elif arg_num.display:
        try:
            num = abs(int(arg_num.display.strip()))
        except ValueError:
            return await app.send_group_message(group, "输入的内容无法转换为整数", quote=source)
    else:
        return await app.send_group_message(group, "未输入要转账的数量", quote=source)

    if num <= 0:
        return await app.send_group_message(group, "转账数量必须大于 0", quote=source)

    if num != int(arg_num.display.strip()):
        await auser.reduce_coin(
            num, force=True, group_id=group.id, source="罚款", detail="非法转账负数"
        )
        return await app.send_group_message(
            group, f"由于你试图转账负数，系统自动将扣除你 {num} 个游戏币", quote=source
        )

    if num > auser.coin:
        return await app.send_group_message(group, "你没有足够的游戏币", quote=source)

    if auser.today_transferred + num > 200:
        return await app.send_group_message(group, "需要转账的数量已超过今日限额", quote=source)

    target_user = await AUserModel.init(at_result.target)
    await auser.reduce_coin(
        num, group_id=group.id, source="转账", detail=f"转账给 {at_result.target}"
    )
    await target_user.add_coin(num, group_id=group.id, source="转账", detail=f"来自 {member.id}")
    auser.today_transferred += num
    await auser.save()  # type: ignore

    await app.send_group_message(
        group, MessageChain(f"已经成功转账 {num} 个游戏币给 {at_result.target}"), quote=source
    )
