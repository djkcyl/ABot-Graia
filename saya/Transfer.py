from graia.saya import Saya, Channel
from graia.ariadne.model import Group, Member
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At, Plain, Source
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    ElementMatch,
    WildcardMatch,
    ArgumentMatch,
)

from config import COIN_NAME
from util.sendMessage import safeSendGroupMessage
from util.control import Permission, Interval, Function
from database.db import reduce_gold, add_gold, trans_all_gold

saya = Saya.current()
channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                {
                    "head": FullMatch(f"赠送{COIN_NAME}"),
                    "at1": ElementMatch(At, optional=True),
                    "anythings1": WildcardMatch(optional=True),
                    "arg1": ArgumentMatch("-all", action="store_true", optional=True),
                },
            )
        ],
        decorators=[
            Function.require("Transfer"),
            Permission.require(),
            Interval.require(5),
        ],
    )
)
async def adminmain(
    group: Group,
    member: Member,
    source: Source,
    at1: ElementMatch,
    anythings1: WildcardMatch,
    arg1: ArgumentMatch,
):
    if not at1.matched:
        await safeSendGroupMessage(
            group, MessageChain.create([Plain("请at需要赠送的对象")]), quote=source
        )
    else:
        to = str(at1.result.target)
        if int(to) == member.id:
            return await safeSendGroupMessage(
                group, MessageChain.create([Plain("请勿向自己赠送")]), quote=source
            )

        if arg1.matched:
            golds = await trans_all_gold(str(member.id), to)
            return await safeSendGroupMessage(
                group,
                MessageChain.create(
                    [
                        Plain(f"已将你的所有{COIN_NAME}赠送给 "),
                        At(int(to)),
                        Plain(f"，共赠送了 {golds} 个"),
                    ]
                ),
                quote=source,
            )

        if anythings1.matched:
            result = anythings1.result.getFirst(Plain).text
            if len(result) > 20:
                return await safeSendGroupMessage(group, MessageChain.create("消息过长"))

            try:
                num = abs(int(result.strip()))
            except Exception:
                return await safeSendGroupMessage(
                    group, MessageChain.create([Plain("请输入正确的数字")]), quote=source
                )
            if "-" in result:
                if await reduce_gold(str(member.id), num, force=True) is None:
                    return await safeSendGroupMessage(
                        group,
                        MessageChain.create(
                            [
                                At(member.id),
                                Plain(f"你的当前{COIN_NAME}不足以扣除 {num}，已清零！"),
                            ]
                        ),
                    )
                else:
                    return await safeSendGroupMessage(
                        group,
                        MessageChain.create(
                            [Plain("已扣除 "), At(member.id), Plain(f" {num} {COIN_NAME}")]
                        ),
                        quote=source,
                    )
            if not 0 < num <= 1000:
                return await safeSendGroupMessage(
                    group,
                    MessageChain.create([Plain("请输入 1-1000 以内的金额")]),
                    quote=source,
                )
            elif await reduce_gold(str(member.id), num):
                await add_gold(to, num)
                await safeSendGroupMessage(
                    group,
                    MessageChain.create(
                        [Plain("你已成功向 "), At(int(to)), Plain(f" 赠送 {num} 个{COIN_NAME}")]
                    ),
                    quote=source,
                )
            else:
                await safeSendGroupMessage(
                    group,
                    MessageChain.create([Plain(f"你的{COIN_NAME}不足，无法赠送")]),
                    quote=source,
                )
        else:
            return await safeSendGroupMessage(
                group, MessageChain.create([Plain("请输入需要赠送的金额")]), quote=source
            )
