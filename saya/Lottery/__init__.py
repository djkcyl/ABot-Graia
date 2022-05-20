import json
import random
import string
import asyncio
import secrets

from pathlib import Path

from loguru import logger
from graia.saya import Channel, Saya
from graia.ariadne.app import Ariadne
from graia.scheduler.timers import crontabify
from graia.broadcast.interrupt.waiter import Waiter
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.model import Friend, Group, Member
from graia.broadcast.interrupt import InterruptControl
from graia.scheduler.saya.schema import SchedulerSchema
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.element import At, Image, Plain, Source
from graia.ariadne.event.message import FriendMessage, GroupMessage
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    ElementMatch,
    ElementResult,
)

from config import COIN_NAME, yaml_data
from database.db import add_gold, reduce_gold
from util.sendMessage import safeSendGroupMessage
from util.control import Function, Interval, Permission

from .certification import decrypt
from .lottery_image import qrdecode, qrgen

saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
inc = InterruptControl(bcc)

BASE = Path(__file__).parent

WAITING = []
if BASE.joinpath("data.json").exists():
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
        inline_dispatchers=[Twilight([FullMatch("购买奖券")])],
        decorators=[
            Function.require("Lottery"),
            Permission.require(),
            Interval.require(),
        ],
    )
)
async def buy_lottery(group: Group, member: Member, source: Source):
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
            MessageChain.create([At(member.id), Plain(f"你的{COIN_NAME}不够，无法购买")]),
            quote=source.id,
        )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([FullMatch("兑换奖券"), "image" @ ElementMatch(Image, optional=True)]),
        ],
        decorators=[
            Function.require("Lottery"),
            Permission.require(),
            Interval.require(),
        ],
    )
)
async def redeem_lottery(
    group: Group, member: Member, image: ElementResult, source: Source
):

    if member.id in WAITING:
        return

    WAITING.append(member.id)

    @Waiter.create_using_function(
        listening_events=[GroupMessage], using_decorators=[Permission.require()]
    )
    async def waiter(
        waiter_group: Group, waiter_member: Member, waiter_message: MessageChain
    ):
        if all([waiter_group.id == group.id, waiter_member.id == member.id]):
            if has_pic := waiter_message.has(Image):
                return waiter_message.getFirst(Image).url

    if image.matched:
        waite_pic = image.result.url
    else:
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

    qrinfo = await qrdecode(waite_pic)
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
                            [Plain(f"你已成功兑换上期奖券，共获得 {str(gold)} 个{COIN_NAME}")]
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

    if yaml_data["Saya"]["Lottery"]["Disabled"]:
        return

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
        inline_dispatchers=[Twilight([FullMatch("奖券开奖")])],
    )
)
async def lo(app: Ariadne, friend: Friend):

    Permission.manual(friend, Permission.MASTER)
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
        friend,
        MessageChain.create(f"本期奖券开奖完毕，中奖号码为\n{winner}"),
    )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("开奖查询")])],
        decorators=[
            Function.require("Lottery"),
            Permission.require(),
            Interval.require(),
        ],
    )
)
async def q_lottery(group: Group):
    lottery = LOTTERY
    winner = lottery["lastweek"]["number"]
    if lottery_len := LOTTERY["lastweek"]["len"]:
        gold = int(lottery_len * 2 * 0.9)
        received = "已领取" if lottery["lastweek"]["received"] else "未领取"
        period = str(lottery["period"] - 1)
        await safeSendGroupMessage(
            group,
            MessageChain.create(
                [
                    Plain("上期开奖信息：\n"),
                    Plain(f"上期期号：{period}\n"),
                    Plain(f"中奖号码：{winner}\n"),
                    Plain(f"奖励：{gold} 个{COIN_NAME}\n"),
                    Plain(f"状态：{received}"),
                ]
            ),
        )
    else:
        await safeSendGroupMessage(
            group,
            MessageChain.create("第一期暂未开奖，请等待每周一开奖后再进行查询"),
        )
