import json
import random
import string
import asyncio
import secrets

from pathlib import Path
from loguru import logger
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.scheduler.timers import crontabify
from graia.ariadne.model import Group, Member
from graia.broadcast.interrupt.waiter import Waiter
from graia.ariadne.message.chain import MessageChain
from graia.broadcast.interrupt import InterruptControl
from graia.scheduler.saya.schema import SchedulerSchema
from graia.ariadne.message.parser.literature import Literature
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.element import At, Plain, Source, Image
from graia.ariadne.event.message import FriendMessage, GroupMessage

from config import yaml_data, group_data
from database.db import add_gold, reduce_gold
from util.control import Interval, Permission
from util.sendMessage import safeSendGroupMessage

from .certification import decrypt
from .lottery_image import qrgen, qrdecode

saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
inc = InterruptControl(bcc)

BASE = Path(__file__).parent

WAITING = []
if not yaml_data["Saya"]["Entertainment"]["Lottery"]:
    pass
elif BASE.joinpath("data.json").exists():
    with BASE.joinpath("data.json").open("r", encoding="UTF-8") as f:
        LOTTERY = json.load(f)
else:
    with BASE.joinpath("data.json").open("w", encoding="UTF-8") as f:
        logger.info("正在初始化奖券数据")
        LOTTERY = {
            "period": 1,
            "lastweek": {"received": False, "number": None, "len": None},
            "week_lottery_list": [],
        }
        json.dump(LOTTERY, f, indent=2, ensure_ascii=False)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Literature("购买奖券")],
        decorators=[Permission.require()],
    )
)
async def buy_lottery(group: Group, member: Member, source: Source):

    if (
        not yaml_data["Saya"]["Entertainment"]["Lottery"]
        and group.id != yaml_data["Basic"]["Permission"]["DebugGroup"]
    ):
        return
    elif (
        yaml_data["Saya"]["Entertainment"]["Disabled"]
        and group.id != yaml_data["Basic"]["Permission"]["DebugGroup"]
    ):
        return
    elif "Entertainment" in group_data[str(group.id)]["DisabledFunc"]:
        return

    if await reduce_gold(str(member.id), 2):
        number = "".join(
            random.sample(string.digits + string.digits + string.digits, 24)
        )
        period = str(LOTTERY["period"])
        lottery = qrgen(str(member.id), number, member.name, period)

        LOTTERY["week_lottery_list"].append(number)
        lottery_len = len(LOTTERY["week_lottery_list"])

        with BASE.joinpath("data.json").open("w", encoding="UTF-8") as f:
            json.dump(LOTTERY, f, indent=2, ensure_ascii=False)
        await safeSendGroupMessage(
            group,
            MessageChain.create(
                [
                    Plain("购买成功，编号为："),
                    Plain(f"\n{number}"),
                    Plain(f"\n当前卡池已有 {lottery_len} 张"),
                    Plain("\n请妥善保管，丢失一概不补"),
                    Image(data_bytes=lottery),
                ]
            ),
            quote=source.id,
        )
    else:
        await safeSendGroupMessage(
            group,
            MessageChain.create([At(member.id), Plain("你的游戏币不够，无法购买")]),
            quote=source.id,
        )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Literature("兑换奖券")],
        decorators=[Permission.require()],
    )
)
async def redeem_lottery(app: Ariadne, group: Group, member: Member, source: Source):

    if member.id in WAITING:
        return

    if (
        not yaml_data["Saya"]["Entertainment"]["Lottery"]
        and group.id != yaml_data["Basic"]["Permission"]["DebugGroup"]
    ):
        return
    elif (
        yaml_data["Saya"]["Entertainment"]["Disabled"]
        and group.id != yaml_data["Basic"]["Permission"]["DebugGroup"]
    ):
        return
    elif "Entertainment" in group_data[str(group.id)]["DisabledFunc"]:
        return

    WAITING.append(member.id)

    @Waiter.create_using_function([GroupMessage])
    async def waiter(
        waiter_group: Group, waiter_member: Member, waiter_message: MessageChain
    ):
        if all([waiter_group.id == group.id, waiter_member.id == member.id]):
            has_pic = waiter_message.has(Image)
            if has_pic:
                get_pic = waiter_message.getFirst(Image).url
                return get_pic

    await safeSendGroupMessage(
        group, MessageChain.create([Plain("请发送需要兑换的奖券")]), quote=source.id
    )

    try:
        waite_pic = await asyncio.wait_for(inc.wait(waiter), timeout=30)
    except asyncio.TimeoutError:
        WAITING.remove(member.id)
        return await safeSendGroupMessage(
            group,
            MessageChain.create([At(member.id), Plain(" 奖券兑换等待超时")]),
            quote=source.id,
        )

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
                    with BASE.joinpath("data.json").open("w", encoding="UTF-8") as f:
                        json.dump(LOTTERY, f, indent=2, ensure_ascii=False)
                    await safeSendGroupMessage(
                        group,
                        MessageChain.create(
                            [Plain(f"你已成功兑换上期奖券，共获得 {str(gold)} 个游戏币")]
                        ),
                    )
                else:
                    await safeSendGroupMessage(
                        group, MessageChain.create([Plain("该奖券已被兑换")])
                    )
            else:
                await safeSendGroupMessage(
                    group, MessageChain.create([Plain("该号码与中奖号码不符")])
                )
        elif period == int(lottery_period):
            await safeSendGroupMessage(
                group, MessageChain.create([Plain("当期奖券请等待每周一开奖后在进行兑换")])
            )
        else:
            await safeSendGroupMessage(group, MessageChain.create([Plain("该奖券已过期")]))
    else:
        await safeSendGroupMessage(
            group, MessageChain.create([Plain("该奖券不为你所有，请勿窃取他人奖券")])
        )
    WAITING.remove(member.id)


@channel.use(SchedulerSchema(crontabify("0 0 * * 1")))
async def something_scheduled(app: Ariadne):
    global LOTTERY
    lottery = LOTTERY
    lottery["period"] += 1
    lottery_len = len(lottery["week_lottery_list"])
    winner = secrets.choice(lottery["week_lottery_list"])
    lottery["lastweek"] = {"received": False, "number": winner, "len": lottery_len}
    lottery["week_lottery_list"] = []

    LOTTERY = lottery
    with BASE.joinpath("data.json").open("w", encoding="UTF-8") as f:
        json.dump(LOTTERY, f, indent=2, ensure_ascii=False)

    await app.sendFriendMessage(
        yaml_data["Basic"]["Permission"]["Master"],
        MessageChain.create([Plain("本期奖券开奖完毕，中奖号码为\n"), Plain(str(winner))]),
    )


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage],
        inline_dispatchers=[Literature("奖券开奖")],
        decorators=[Permission.require(Permission.MASTER)],
    )
)
async def lo(app: Ariadne):
    global LOTTERY
    lottery = LOTTERY
    lottery["period"] += 1
    lottery_len = len(lottery["week_lottery_list"])
    winner = secrets.choice(lottery["week_lottery_list"])
    lottery["lastweek"] = {"received": False, "number": winner, "len": lottery_len}
    lottery["week_lottery_list"] = []

    LOTTERY = lottery
    with BASE.joinpath("data.json").open("w", encoding="UTF-8") as f:
        json.dump(LOTTERY, f, indent=2, ensure_ascii=False)

    await app.sendFriendMessage(
        yaml_data["Basic"]["Permission"]["Master"],
        MessageChain.create([Plain("本期奖券开奖完毕，中奖号码为\n"), Plain(str(winner))]),
    )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Literature("开奖查询")],
        decorators=[Permission.require(), Interval.require()],
    )
)
async def q_lottery(group: Group):

    if (
        not yaml_data["Saya"]["Entertainment"]["Lottery"]
        and group.id != yaml_data["Basic"]["Permission"]["DebugGroup"]
    ):
        return
    elif (
        yaml_data["Saya"]["Entertainment"]["Disabled"]
        and group.id != yaml_data["Basic"]["Permission"]["DebugGroup"]
    ):
        return
    elif "Entertainment" in group_data[str(group.id)]["DisabledFunc"]:
        return

    lottery = LOTTERY
    period = str(lottery["period"] - 1)
    winner = lottery["lastweek"]["number"]
    lottery_len = LOTTERY["lastweek"]["len"]
    gold = int(lottery_len * 2 * 0.9)
    received = "已领取" if lottery["lastweek"]["received"] else "未领取"
    await safeSendGroupMessage(
        group,
        MessageChain.create(
            [
                Plain("上期开奖信息：\n"),
                Plain(f"上期期号：{period}\n"),
                Plain(f"中奖号码：{winner}\n"),
                Plain(f"奖励：{gold} 个游戏币\n"),
                Plain(f"状态：{received}"),
            ]
        ),
    )
