import time
import random

from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.element import At, Plain
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.model import Friend, Group, Member
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import FriendMessage, GroupMessage
from graia.ariadne.message.parser.twilight import FullMatch, Twilight

from config import COIN_NAME
from util.sendMessage import safeSendGroupMessage
from database.db import add_gold, all_sign_num, sign
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
        i = random.randint(1, 10)
        gold_add = random.randint(9, 21) if i == 1 else random.randint(5, 12)
        await add_gold(member.id, gold_add)
        sign_text = f"今日签到成功！\n本次签到获得{COIN_NAME} {gold_add} 个"
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


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage],
        inline_dispatchers=[Twilight([FullMatch("签到率查询")])],
    )
)
async def inquire(app: Ariadne, friend: Friend):
    Permission.manual(friend, Permission.MASTER)
    sign_info = await all_sign_num()
    await app.sendFriendMessage(
        friend,
        MessageChain.create(
            [
                Plain(f"共有 {str(sign_info[0])} / {str(sign_info[1])} 人完成了签到，"),
                Plain(f"签到率为 {'{:.2%}'.format(sign_info[0]/sign_info[1])}"),
            ]
        ),
    )
