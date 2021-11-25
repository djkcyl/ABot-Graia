from graia.saya import Saya, Channel
from graia.ariadne.model import Group, Member
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At, Plain, Source
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import Sparkle, Twilight
from graia.ariadne.message.parser.pattern import FullMatch, RegexMatch

from config import yaml_data, group_data
from util.control import Permission, Interval
from util.sendMessage import safeSendGroupMessage
from database.db import reduce_gold, add_gold, trans_all_gold

saya = Saya.current()
channel = Channel.current()


class EconomySparkle(Sparkle):
    header = FullMatch("赠送游戏币")
    space = FullMatch(" ", optional=True)
    anythings1 = RegexMatch(r".*?", optional=True)
    arg1 = FullMatch("-all", optional=True)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(EconomySparkle)],
        decorators=[Permission.require(), Interval.require(5)],
    )
)
async def adminmain(
    group: Group,
    member: Member,
    source: Source,
    sparkle: Sparkle,
):

    if (
        yaml_data["Saya"]["Entertainment"]["Disabled"]
        and group.id != yaml_data["Basic"]["Permission"]["DebugGroup"]
    ):
        return
    elif "Entertainment" in group_data[str(group.id)]["DisabledFunc"]:
        return

    saying: EconomySparkle = sparkle
    print(saying)

    if not saying.anythings1.result.has(At):
        await safeSendGroupMessage(
            group, MessageChain.create([Plain("请at需要赠送的对象")]), quote=source
        )
    else:
        to = str(saying.anythings1.result.getFirst(At).target)
        if int(to) == member.id:
            return await safeSendGroupMessage(
                group, MessageChain.create([Plain("请勿向自己赠送")]), quote=source
            )

        if saying.arg1.matched:
            golds = await trans_all_gold(str(member.id), to)
            return await safeSendGroupMessage(
                group,
                MessageChain.create(
                    [
                        Plain("已将你的所有游戏币赠送给 "),
                        At(int(to)),
                        Plain(f"，共赠送了 {golds} 个"),
                    ]
                ),
                quote=source,
            )

        if saying.anythings1.matched:
            result = MessageChain.create(
                saying.anythings1.result.get(Plain)
            ).asDisplay()
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
                                Plain(f"你的当前游戏币不足以扣除 {num}，已清零！"),
                            ]
                        ),
                    )
                else:
                    return await safeSendGroupMessage(
                        group,
                        MessageChain.create(
                            [Plain("已扣除 "), At(member.id), Plain(f" {num} 游戏币")]
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
                        [Plain("你已成功向 "), At(int(to)), Plain(f" 赠送 {num} 个游戏币")]
                    ),
                    quote=source,
                )
            else:
                await safeSendGroupMessage(
                    group, MessageChain.create([Plain("你的游戏币不足，无法赠送")]), quote=source
                )
        else:
            return await safeSendGroupMessage(
                group, MessageChain.create([Plain("请输入需要赠送的金额")]), quote=source
            )
