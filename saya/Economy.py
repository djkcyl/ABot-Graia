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
from database.db import reduce_gold, add_gold
from util.sendMessage import safeSendGroupMessage

saya = Saya.current()
channel = Channel.current()


class Sparkle1(Sparkle):
    perfix = FullMatch("赠送游戏币")
    space1 = FullMatch(" ", optional=True)
    element1 = RegexMatch("\b\\d+\b", optional=True)
    space2 = FullMatch(" ", optional=True)
    any1 = RegexMatch(r"\s*-?\d+", optional=True)


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Twilight(Sparkle1)],
                            decorators=[Permission.require(), Interval.require(5)]))
async def adminmain(group: Group, member: Member, message: MessageChain, source: Source, sparkle: Sparkle):

    if yaml_data['Saya']['Entertainment']['Disabled']:
        return
    elif 'Entertainment' in group_data[str(group.id)]['DisabledFunc']:
        return

    saying: Sparkle1 = sparkle
    print(saying)

    if not message.has(At):
        await safeSendGroupMessage(group, MessageChain.create([
            Plain("请at需要赠送的对象")
        ]), quote=source.id)
    else:
        to = str(message.getFirst(At).target)
        if int(to) == member.id:
            return await safeSendGroupMessage(group, MessageChain.create([
                Plain("请勿向自己赠送")
            ]), quote=source.id)

        if saying.any1.matched:
            result = saying.any1.result.getFirst(Plain).text
            if len(result) > 20:
                return await safeSendGroupMessage(group, MessageChain.create("消息过长"))
            num = abs(int(result.strip()))
            if "-" in result:
                if await reduce_gold(str(member.id), num, force=True) is None:
                    return await safeSendGroupMessage(group, MessageChain.create([
                        At(member.id),
                        Plain(f"你的当前游戏币不足以扣除 {num}，已清零！"),
                    ]))
                else:
                    return await safeSendGroupMessage(group, MessageChain.create([
                        Plain("已扣除 "),
                        At(member.id),
                        Plain(f" {num} 游戏币")
                    ]))
            if not 0 < num <= 1000:
                return await safeSendGroupMessage(group, MessageChain.create([
                    Plain("请输入 1-1000 以内的金额")
                ]), quote=source.id)
            elif await reduce_gold(str(member.id), num):
                await add_gold(to, num)
                await safeSendGroupMessage(group, MessageChain.create([
                    Plain("你已成功向 "),
                    At(int(to)),
                    Plain(f" 赠送 {num} 个游戏币")
                ]), quote=source.id)
            else:
                await safeSendGroupMessage(group, MessageChain.create([
                    Plain("你的游戏币不足，无法赠送")
                ]), quote=source.id)
        else:
            return await safeSendGroupMessage(group, MessageChain.create([
                Plain("请输入需要赠送的金额")
            ]), quote=source.id)
