from graia.saya import Saya, Channel
from graia.application.group import Group, Member
from graia.application import GraiaMiraiApplication
from graia.application.event.messages import GroupMessage
from graia.application.message.parser.kanata import Kanata
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.parser.signature import FullMatch, OptionalParam
from graia.application.message.elements.internal import MessageChain, At, Plain, Source

from config import yaml_data, group_data
from util.limit import member_limit_check
from util.UserBlock import group_black_list_block
from datebase.db import reduce_gold, add_gold

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Kanata([FullMatch("赠送游戏币"), OptionalParam("saying")])],
                            headless_decorators=[member_limit_check(5), group_black_list_block()]))
async def adminmain(app: GraiaMiraiApplication, group: Group, member: Member, message: MessageChain, source: Source):

    if yaml_data['Saya']['Entertainment']['Disabled']:
        return
    elif 'Entertainment' in group_data[group.id]['DisabledFunc']:
        return

    if not message.has(At):
        await app.sendGroupMessage(group, MessageChain.create([
            Plain("请at需要赠送的对象")
        ]), quote=source)
    else:
        to = str(message.getFirst(At).target)
        if int(to) == member.id:
            return await app.sendGroupMessage(group, MessageChain.create([
                Plain("请勿向自己赠送")
            ]), quote=source)
        # print(message.getOne(Plain, 1))
        try:
            num = int(message.get(Plain)[-1].text)
            if not 0 < num <= 1000:
                return await app.sendGroupMessage(group, MessageChain.create([
                    Plain("请输入 1-1000 以内的金额")
                ]), quote=source)
        except:
            return await app.sendGroupMessage(group, MessageChain.create([
                Plain("请输入需要赠送的金额")
            ]), quote=source)

        if await reduce_gold(str(member.id), num):
            await add_gold(to, num)
            await app.sendGroupMessage(group, MessageChain.create([
                Plain("你已成功向 "),
                At(int(to)),
                Plain(f" 赠送 {num} 个游戏币")
            ]), quote=source)
        else:
            await app.sendGroupMessage(group, MessageChain.create([
                Plain("你的游戏币不足，无法赠送")
            ]), quote=source)
