import os
import json
import random
import string
import asyncio
import time

from graia.saya import Saya, Channel
from graia.application.friend import Friend
from graia.scheduler.timers import crontabify
from graia.application.group import Group, Member
from graia.application import GraiaMiraiApplication
from graia.broadcast.interrupt.waiter import Waiter
from graia.broadcast.interrupt import InterruptControl
from graia.scheduler.saya.schema import SchedulerSchema
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.parser.literature import Literature
from graia.application.event.messages import FriendMessage, GroupMessage
from graia.application.message.elements.internal import At, Image_UnsafeBytes, Plain, MessageChain, Source, Image

from datebase.db import add_gold, reduce_gold
from config import sendmsg, yaml_data, group_data

from .certification import decrypt
from .lottery_image import qrgen, qrdecode

saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
inc = InterruptControl(bcc)

WAITING = []
if os.path.exists("./saya/Lottery/data.json"):
    with open("./saya/Lottery/data.json", "r") as f:
        LOTTERY = json.load(f)
else:
    with open("./saya/Lottery/data.json", "w") as f:
        print("正在初始化奖券数据")
        LOTTERY = {
            "period": 1,
            "lastweek": {
                "received": False,
                "number": None,
                "len": None
            },
            "week_lottery_list": []
        }
        json.dump(LOTTERY, f, indent=2, ensure_ascii=False)


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("购买奖券")]))
async def buy_lottery(app: GraiaMiraiApplication, group: Group, member: Member, source: Source):

    if yaml_data['Saya']['Lottery']['Disabled']:
        return await sendmsg(app=app, group=group)
    elif 'Lottery' in group_data[group.id]['DisabledFunc']:
        return await sendmsg(app=app, group=group)

    if await reduce_gold(str(member.id), 2):
        number = ''.join(random.sample(string.digits+string.digits+string.digits, 24))
        period = str(LOTTERY["period"])
        lottery = qrgen(str(member.id), number, member.name, period)

        LOTTERY["week_lottery_list"].append(number)
        lottery_len = len(LOTTERY["week_lottery_list"])

        with open("./saya/Lottery/data.json", "w") as f:
            json.dump(LOTTERY, f, indent=2, ensure_ascii=False)
        await app.sendGroupMessage(group, MessageChain.create([
            Plain("购买成功，编号为："),
            Plain(f"\n{number}"),
            Plain(f"\n当前卡池已有 {lottery_len} 张"),
            Plain(f"\n请妥善保管，丢失一概不补"),
            Image_UnsafeBytes(lottery.getvalue())
        ]), quote=source)
    else:
        await app.sendGroupMessage(group, MessageChain.create([
            At(member.id),
            Plain("你的游戏币不够，无法购买")
        ]), quote=source)


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("兑换奖券")]))
async def redeem_lottery(app: GraiaMiraiApplication, group: Group, member: Member, source: Source):

    if member.id in WAITING:
        return

    if yaml_data['Saya']['Lottery']['Disabled']:
        return await sendmsg(app=app, group=group)
    elif 'Lottery' in group_data[group.id]['DisabledFunc']:
        return await sendmsg(app=app, group=group)

    WAITING.append(member.id)

    @Waiter.create_using_function([GroupMessage])
    async def waiter(waiter_group: Group, waiter_member: Member, waiter_message: MessageChain):
        if all([waiter_group.id == group.id, waiter_member.id == member.id]):
            has_pic = waiter_message.has(Image)
            if has_pic:
                get_pic = waiter_message.getFirst(Image).url
                return get_pic

    await app.sendGroupMessage(group, MessageChain.create([
        Plain("请发送需要兑换的奖券")
    ]), quote=source)

    try:
        waite_pic = await asyncio.wait_for(inc.wait(waiter), timeout=30)
    except asyncio.TimeoutError:
        WAITING.remove(member.id)
        return await app.sendGroupMessage(group, MessageChain.create([
            At(member.id),
            Plain(" 奖券兑换等待超时")
        ]), quote=source)

    qrinfo = qrdecode(waite_pic)
    image_info = decrypt(qrinfo)
    lottery_qq, lottery_id, lottery_period = image_info.split("|")
    if lottery_qq == str(member.id):
        period = LOTTERY["period"]
        if int(lottery_period) == period - 1:
            if LOTTERY["lastweek"]["number"] == lottery_id:
                if not LOTTERY["lastweek"]["received"]:
                    lottery_len = LOTTERY["lastweek"]["len"]
                    gold = int(lottery_len * 2 * 0.9)
                    await add_gold(lottery_qq, gold)
                    LOTTERY["lastweek"]["received"] = True
                    with open("./saya/Lottery/data.json", "w") as f:
                        json.dump(LOTTERY, f, indent=2, ensure_ascii=False)
                    await app.sendGroupMessage(group, MessageChain.create([Plain("你已成功兑换上期奖券")]))
                else:
                    await app.sendGroupMessage(group, MessageChain.create([Plain("该奖券已被兑换")]))
            else:
                await app.sendGroupMessage(group, MessageChain.create([Plain("该号码与中奖号码不符")]))
        elif period == int(lottery_period):
            await app.sendGroupMessage(group, MessageChain.create([Plain("当期奖券请等待每周一开奖后在进行兑换")]))
        else:
            await app.sendGroupMessage(group, MessageChain.create([Plain("该奖券已过期")]))
    else:
        await app.sendGroupMessage(group, MessageChain.create([Plain("该奖券不为你所有，请勿窃取他人奖券")]))
    WAITING.remove(member.id)

@channel.use(SchedulerSchema(crontabify("0 0 * * 1")))
async def something_scheduled(app: GraiaMiraiApplication):
    global LOTTERY
    lottery = LOTTERY
    lottery["period"] += 1
    lottery_len = len(lottery["week_lottery_list"])
    winner = random.choice(lottery["week_lottery_list"])
    lottery["lastweek"] = {
        "received": False,
        "number": winner,
        "len": lottery_len
    }
    lottery["week_lottery_list"] = []

    LOTTERY = lottery
    with open("./saya/Lottery/data.json", "w") as f:
        json.dump(LOTTERY, f, indent=2, ensure_ascii=False)

    await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
        Plain("本期奖券开奖完毕，中奖号码为\n"),
        Plain(str(winner))
    ]))

    ft = time.time()
    groupList = await app.groupList()
    for group in groupList:
        if group.id not in [885355617, 780537426, 474769367, 690211045, 855895642]:
            try:
                await app.sendGroupMessage(group.id, MessageChain.create([
                    Plain(f"{str(group.id)}"),
                    Plain("\n本期奖券开奖完毕，中奖号码为\n"),
                    Plain(str(winner))
                ]))
            except Exception as err:
                await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
                    Plain(f"{group.id} 的开奖信息发送失败\n{err}")
                ]))
            await asyncio.sleep(random.uniform(5, 7))
    tt = time.time()
    times = str(tt - ft)
    await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
        Plain(f"开奖信息已发送完成，耗时 {times} 秒")
    ]))


@channel.use(ListenerSchema(listening_events=[FriendMessage], inline_dispatchers=[Literature("开奖")]))
async def something_scheduled(app: GraiaMiraiApplication, friend: Friend):
    if friend.id == yaml_data['Basic']['Permission']['Master']:
        global LOTTERY
        lottery = LOTTERY
        lottery["period"] += 1
        lottery_len = len(lottery["week_lottery_list"])
        winner = random.choice(lottery["week_lottery_list"])
        lottery["lastweek"] = {
            "received": False,
            "number": winner,
            "len": lottery_len
        }
        lottery["week_lottery_list"] = []

        LOTTERY = lottery
        with open("./saya/Lottery/data.json", "w") as f:
            json.dump(LOTTERY, f, indent=2, ensure_ascii=False)

        await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
            Plain("本期奖券开奖完毕，中奖号码为\n"),
            Plain(str(winner))
        ]))