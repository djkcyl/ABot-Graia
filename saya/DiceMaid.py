import re
import heapq
import random

from graia.saya import Saya, Channel
from graia.application import GraiaMiraiApplication
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.event.messages import Group, GroupMessage
from graia.application.message.elements.internal import Plain, MessageChain

from util.limit import manual_limit
from util.UserBlock import black_list_block
from config import sendmsg, yaml_data, group_data

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            headless_decorators=[black_list_block()]))
async def dice(app: GraiaMiraiApplication, group: Group, message: MessageChain):

    if message.asDisplay()[:2] == ".r":
        if yaml_data['Saya']['DiceMaid']['Disabled']:
            return await sendmsg(app=app, group=group)
        elif 'DiceMaid' in group_data[group.id]['DisabledFunc']:
            return await sendmsg(app=app, group=group)
        manual_limit(group.id, "DiceMaid", 3)

        saying = message.asDisplay()

        pattern = re.compile(r"^.r(?P<times>\d+)?d?(?P<maxvalue>\d+)?k?(?P<kiswhat>\d+)?")
        match = re.match(pattern, saying)

        r = match.group('times')
        d = match.group('maxvalue')
        k = match.group('kiswhat')

        if not r:
            dr = 1
        elif 1 < int(r) < 100:
            dr = int(r)
        else:
            return await app.sendGroupMessage(group, MessageChain.create([
                Plain(f"一次仅可投掷 1 - 100 个骰子")
            ]))

        if not d:
            dd = 100
        elif 0 < int(d) < 1000:
            dd = int(d)
        else:
            return await app.sendGroupMessage(group, MessageChain.create([
                Plain(f"仅可投掷 1 - 1000 面的骰子")
            ]))

        if not k:
            dk = 0
        elif int(k) > dr:
            return await app.sendGroupMessage(group, MessageChain.create([
                Plain(f"你输入的值有误，取最大数（k）不可大于总骰子数（r）")
            ]))
        else:
            dk = int(k)

        dice_list = []
        for _ in range(dr):
            dice = random.randint(1, dd)
            dice_list.append(dice)

        if k:
            max_dice = heapq.nlargest(dk, dice_list)
            num_list_new = map(lambda x: str(x), max_dice)
            max_dice_str = ", ".join(num_list_new)
            dice_sum = sum(max_dice)
            await app.sendGroupMessage(group, MessageChain.create([
                Plain(
                    f"你投出 {dr} 个骰子\n其中最大的 {dk} 个为：{max_dice_str}\n它们的和为 {dice_sum}")
            ]))
        elif dr == 1:
            await app.sendGroupMessage(group, MessageChain.create([
                Plain(f"你投出 1 个骰子\n它的值为 {dice_list[0]}")
            ]))
        else:
            dice_list_new = map(lambda x: str(x), dice_list)
            dice_list_str = ", ".join(dice_list_new)
            dice_sum = sum(dice_list)
            await app.sendGroupMessage(group, MessageChain.create([
                Plain(f"你投出 {dr} 个骰子\n他们分别为：{dice_list_str}\n它们的和为：{dice_sum}")
            ]))
