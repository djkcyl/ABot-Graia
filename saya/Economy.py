from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
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
from util.sendMessage import selfSendGroupMessage

saya = Saya.current()
channel = Channel.current()


class Sparkle1(Sparkle):
    perfix = FullMatch("赠送游戏币")
    any1 = RegexMatch(".*", optional=True)


twilight = Twilight(Sparkle1)


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[twilight],
                            decorators=[Permission.require(), Interval.require(5)]))
async def adminmain(app: Ariadne, group: Group, member: Member, message: MessageChain, source: Source):

    if yaml_data['Saya']['Entertainment']['Disabled']:
        return
    elif 'Entertainment' in group_data[str(group.id)]['DisabledFunc']:
        return

    saying: Sparkle1 = twilight.gen_sparkle(message)

    if not message.has(At):
        await selfSendGroupMessage(group, MessageChain.create([
            Plain("请at需要赠送的对象")
        ]), quote=source.id)
    else:
        to = str(message.getFirst(At).target)
        if int(to) == member.id:
            return await selfSendGroupMessage(group, MessageChain.create([
                Plain("请勿向自己赠送")
            ]), quote=source.id)

        if saying.any2.matched:
            num = int(saying.any2.result.getFirst(Plain).text.strip())
            if not 0 < num <= 1000:
                return await selfSendGroupMessage(group, MessageChain.create([
                    Plain("请输入 1-1000 以内的金额")
                ]), quote=source.id)
            elif await reduce_gold(str(member.id), num):
                await add_gold(to, num)
                await selfSendGroupMessage(group, MessageChain.create([
                    Plain("你已成功向 "),
                    At(int(to)),
                    Plain(f" 赠送 {num} 个游戏币")
                ]), quote=source.id)
            else:
                await selfSendGroupMessage(group, MessageChain.create([
                    Plain("你的游戏币不足，无法赠送")
                ]), quote=source.id)
        else:
            return await selfSendGroupMessage(group, MessageChain.create([
                Plain("请输入需要赠送的金额")
            ]), quote=source.id)
