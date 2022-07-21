import time
import random

from graia.saya import Channel
from graia.ariadne.model import Group, Member
from graia.ariadne.message.element import At, Plain
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import FullMatch, Twilight

from config import COIN_NAME
from database.db import add_gold, sign, get_info
from util.sendMessage import safeSendGroupMessage
from util.control import Function, Interval, Permission

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("签到")])],
        decorators=[Function.require("Sign"), Permission.require(), Interval.require()],
    )
)
async def main(group: Group, member: Member):
    if await sign(member.id):
        user = await get_info(member.id)
        if user[5] % 30 == 0:
            continue_reward = random.randint(0, 60)
            continue_text = f"额外获得 {continue_reward} {COIN_NAME}"
        elif user[5] % 7 == 0:
            continue_reward = random.randint(0, 15)
            continue_text = f"额外获得 {continue_reward} {COIN_NAME}"
        else:
            continue_reward = 0
            first_sign = f"首次签到赠送 60 {COIN_NAME}," if user[2] == 1 else ""
            remaining_days = min(30 - (user[5] % 30), 7 - (user[5] % 7))
            continue_text = f"{first_sign}继续签到 {remaining_days} 天将赠送额外 {COIN_NAME}"

        first_sign_gold = 60 if user[2] == 1 else 0
        gold_add = (
            random.randint(9, 21) if random.randint(1, 10) == 1 else random.randint(5, 12)
        ) + continue_reward + first_sign_gold
        await add_gold(member.id, gold_add)
        sign_text = (
            f"今日签到成功！\n本次签到获得 {COIN_NAME} {gold_add} 个\n你已连续签到{user[5]}天，{continue_text}"
        )
    else:
        sign_text = "今天你已经签到过了，不能贪心，凌晨4点以后再来吧！"

    now_localtime = time.strftime("%H:%M:%S", time.localtime())
    if "06:00:00" < now_localtime < "08:59:59":
        time_nick = "早上好"
    elif "09:00:00" < now_localtime < "11:59:59":
        time_nick = "上午好"
    elif "12:00:00" < now_localtime < "13:59:59":
        time_nick = "中午好"
    elif "14:00:00" < now_localtime < "17:59:59":
        time_nick = "下午好"
    elif "18:00:00" < now_localtime < "23:59:59":
        time_nick = "晚上好"
    else:
        time_nick = "唔。。还没睡吗？要做一个乖孩子，早睡早起身体好喔！晚安❤"

    await safeSendGroupMessage(
        group,
        MessageChain.create(
            [Plain(f"{time_nick}，"), At(member.id), Plain(f"\n{sign_text}")]
        ),
    )
