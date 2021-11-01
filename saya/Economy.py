from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group, Member
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At, Plain, Source
from graia.ariadne.message.parser.literature import Literature
from graia.saya.builtins.broadcast.schema import ListenerSchema

from config import yaml_data, group_data
from util.limit import member_limit_check
from util.UserBlock import group_black_list_block
from database.db import reduce_gold, add_gold

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Literature("赠送游戏币")],
                            headless_decorators=[member_limit_check(5), group_black_list_block()]))
async def adminmain(app: Ariadne, group: Group, member: Member, message: MessageChain, source: Source):

    if yaml_data['Saya']['Entertainment']['Disabled']:
        return
    elif 'Entertainment' in group_data[group.id]['DisabledFunc']:
        return

    saying = message.asDisplay().split()

    if not message.has(At):
        await app.sendGroupMessage(group, MessageChain.create([
            Plain("请at需要赠送的对象")
        ]), quote=source.id)
    else:
        to = str(message.getFirst(At).target)
        if int(to) == member.id:
            return await app.sendGroupMessage(group, MessageChain.create([
                Plain("请勿向自己赠送")
            ]), quote=source.id)
        try:
            num = int(saying[2])
            if not 0 < num <= 1000:
                return await app.sendGroupMessage(group, MessageChain.create([
                    Plain("请输入 1-1000 以内的金额")
                ]), quote=source.id)
        except:
            return await app.sendGroupMessage(group, MessageChain.create([
                Plain("请输入需要赠送的金额")
            ]), quote=source.id)

        if await reduce_gold(str(member.id), num):
            await add_gold(to, num)
            await app.sendGroupMessage(group, MessageChain.create([
                Plain("你已成功向 "),
                At(int(to)),
                Plain(f" 赠送 {num} 个游戏币")
            ]), quote=source.id)
        else:
            await app.sendGroupMessage(group, MessageChain.create([
                Plain("你的游戏币不足，无法赠送")
            ]), quote=source.id)
