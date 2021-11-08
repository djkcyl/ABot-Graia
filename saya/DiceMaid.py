import re
import heapq
import random

from graia.saya import Saya, Channel
from graia.ariadne.message.element import Plain
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import Group, GroupMessage
from graia.ariadne.message.parser.pattern import RegexMatch
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import Sparkle, Twilight

from config import yaml_data, group_data
from util.control import Permission, Interval
from util.sendMessage import selfSendGroupMessage

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Twilight(Sparkle([RegexMatch(r".r(\d+)?d?(\d+)?k?(\d+)?")]))],
                            decorators=[Permission.require(Permission.MASTER), Interval.require(5)]))
async def dice(group: Group, message: MessageChain):

    if yaml_data['Saya']['DiceMaid']['Disabled']:
        return
    elif 'DiceMaid' in group_data[str(group.id)]['DisabledFunc']:
        return

    saying = message.asDisplay()

    pattern = re.compile(r"^.r(?P<times>\d+)?d?(?P<maxvalue>\d+)?k?(?P<kiswhat>\d+)?")
    match = re.match(pattern, saying)

    r = match.group('times')
    d = match.group('maxvalue')
    k = match.group('kiswhat')

    if not r:
        dr = 1
    elif 0 < int(r) < 101:
        dr = int(r)
    elif int(r) == 300 and int(k) == 10:
        dr = 300
    else:
        return await selfSendGroupMessage(group, MessageChain.create([
            Plain("一次仅可投掷 1 - 100 个骰子")
        ]))

    if not d:
        dd = 100
    elif 0 < int(d) < 1001:
        dd = int(d)
    else:
        return await selfSendGroupMessage(group, MessageChain.create([
            Plain("仅可投掷 1 - 1000 面的骰子")
        ]))

    if not k:
        dk = 0
    elif 1 < int(k) < dr:
        dk = int(k)
    else:
        return await selfSendGroupMessage(group, MessageChain.create([
            Plain("你输入的值有误，取最大数（k）不可大于总骰子数（r）或小于 2")
        ]))

    dice_list = []
    for _ in range(dr):
        dice = random.randint(1, dd)
        dice_list.append(dice)

    if k:
        max_dice = heapq.nlargest(dk, dice_list)
        num_list_new = map(lambda x: str(x), max_dice)
        max_dice_str = ", ".join(num_list_new)
        dice_sum = sum(max_dice)
        await selfSendGroupMessage(group, MessageChain.create([
            Plain(
                f"你投出 {dr} 个骰子\n其中最大的 {dk} 个为：{max_dice_str}\n它们的和为 {dice_sum}")
        ]))
    elif dr == 1:
        await selfSendGroupMessage(group, MessageChain.create([
            Plain(f"你投出 1 个骰子\n它的值为 {dice_list[0]}")
        ]))
    else:
        dice_list_new = map(lambda x: str(x), dice_list)
        dice_list_str = ", ".join(dice_list_new)
        dice_sum = sum(dice_list)
        await selfSendGroupMessage(group, MessageChain.create([
            Plain(f"你投出 {dr} 个骰子\n他们分别为：{dice_list_str}\n它们的和为：{dice_sum}")
        ]))
