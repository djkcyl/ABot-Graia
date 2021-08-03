import re
import heapq
import random

from graia.saya import Saya, Channel
from graia.application import GraiaMiraiApplication
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.event.messages import Group, GroupMessage
from graia.application.message.elements.internal import Plain, MessageChain

from config import sendmsg, yaml_data, group_data

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def dice(app: GraiaMiraiApplication, group: Group, message: MessageChain):

    if message.asDisplay()[:2] == ".r":
        if yaml_data['Saya']['DiceMaid']['Disabled']:
            return await sendmsg(app=app, group=group)
        elif 'DiceMaid' in group_data[group.id]['DisabledFunc']:
            return await sendmsg(app=app, group=group)

        saying = message.asDisplay()

        pattern = re.compile(
            r"^.r(?P<times>\d+)?d?(?P<maxvalue>\d+)?k?(?P<kiswhat>\d+)?")
        match = re.match(pattern, saying)

        r = match.group('times')
        d = match.group('maxvalue')
        k = match.group('kiswhat')

        if not r:
            dr = 1
        else:
            dr = int(r)

        if not d:
            dd = 100
        elif int(d) > 100:
            return await app.sendGroupMessage(group, MessageChain.create([
                Plain(f"一次仅可投掷 100 个以内的骰子")
            ]))
        else:
            dd = int(d)

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
