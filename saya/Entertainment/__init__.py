import time
import random

from graia.saya import Saya, Channel
from graia.application.friend import Friend
from graia.scheduler.timers import crontabify
from graia.application.group import Group, Member
from graia.application import GraiaMiraiApplication
from graia.scheduler.saya.schema import SchedulerSchema
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.parser.literature import Literature
from graia.application.event.messages import GroupMessage, FriendMessage
from graia.application.message.elements.internal import Plain, MessageChain


from config import yaml_data, group_data
from datebase.db import sign, add_gold, get_info, add_talk, reset_sign, all_sign_num, give_all_gold

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("签到")]))
async def main(app: GraiaMiraiApplication, group: Group, member: Member):
    if await sign(str(member.id)):
        i = random.randint(1, 10)
        if i == 1:
            gold_add = random.randint(9, 21)
        else:
            gold_add = random.randint(5, 12)
        await add_gold(str(member.id), gold_add)
        sign_text = f"今日签到成功！\n本次签到获得游戏币 {str(gold_add)} 个"
    else:
        sign_text = "今天你已经签到过了，不能贪心，凌晨4点以后再来吧！"

    if yaml_data['Saya']['Entertainment']['Disabled']:
        return
    elif 'Entertainment' in group_data[group.id]['DisabledFunc']:
        return

    user_info = await get_info(str(member.id))
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
        time_nick = f"（假装现在是晚上11点）唔。。还没睡吗？要像{yaml_data['Basic']['BotName']}一样做一个乖孩子，早睡早起身体好喔！晚安❤"

    await app.sendGroupMessage(group, MessageChain.create([
        Plain(f"{time_nick}，{member.name}"),
        Plain(f"\n{sign_text}"),
        Plain(f"\n当前共有 {str(user_info[3])} 个游戏币"),
        Plain(f"\n你已累计签到 {str(user_info[2])} 天"),
        Plain(f"\n从有记录以来你共有 {str(user_info[4])} 次发言"),
        Plain("\n当前游戏币可在群内发起 <你画我猜>")
    ]))


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def main(member: Member):
    await add_talk(str(member.id))


@channel.use(SchedulerSchema(crontabify("0 4 * * *")))
async def reset(app: GraiaMiraiApplication):
    sign_info = await all_sign_num()
    await reset_sign()
    await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
        Plain(f"签到重置成功，昨日共有 {str(sign_info[0])} / {str(sign_info[1])} 人完成了签到，"),
        Plain(f"签到率为 {'{:.2%}'.format(sign_info[0]/sign_info[1])}")
    ]))


@channel.use(ListenerSchema(listening_events=[FriendMessage], inline_dispatchers=[Literature("签到率查询")]))
async def main(app: GraiaMiraiApplication, friend: Friend):
    if friend.id == yaml_data['Basic']['Permission']['Master']:
        sign_info = await all_sign_num()
        await app.sendFriendMessage(friend, MessageChain.create([
            Plain(f"共有 {str(sign_info[0])} / {str(sign_info[1])} 人完成了签到，"),
            Plain(f"签到率为 {'{:.2%}'.format(sign_info[0]/sign_info[1])}")
        ]))


@channel.use(ListenerSchema(listening_events=[FriendMessage], inline_dispatchers=[Literature("全员充值")]))
async def main(app: GraiaMiraiApplication, friend: Friend, message: MessageChain):
    if friend.id == yaml_data['Basic']['Permission']['Master']:
        saying = message.asDisplay().split()
        await give_all_gold(int(saying[1]))
        await app.sendFriendMessage(friend, MessageChain.create([
            Plain(f"已向所有人充值 {saying[1]} 个游戏币")
        ]))