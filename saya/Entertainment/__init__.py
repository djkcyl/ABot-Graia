import random
import time

from graia.saya import Saya, Channel
from graia.application.event.mirai import *
from graia.application.event.messages import *
from graia.application import GraiaMiraiApplication
from graia.application.message.elements.internal import *
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.parser.literature import Literature
from graia.scheduler.saya.schema import SchedulerSchema
from graia.scheduler.timers import crontabify

from config import yaml_data
from datebase.db import sign, add_gold, get_info, add_talk, reset_sign

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("签到")]))
async def main(app: GraiaMiraiApplication, group: Group, member: Member):
    if await sign(str(member.id)):
        i = random.randint(1,10)
        if i == 1:
            gold_add = random.randint(4, 16)
        else:
            gold_add = random.randint(2, 8)
        await add_gold(str(member.id), gold_add)
        sign_text = f"今日签到成功！\n本次签到获得游戏币 {str(gold_add)} 个"
    else:
        sign_text = "今天你已经签到过了，不能贪心，凌晨4点以后再来吧！"
        
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
        Plain(f"{time_nick}。{member.name}"),
        Plain(f"\n{sign_text}"),
        Plain(f"\n你已累计签到 {str(user_info[2])} 天"),
        Plain(f"\n当前游戏币：{str(user_info[3])} 个"),
        Plain(f"\n从有记录以来你共有 {str(user_info[4])} 次发言")
    ]))
    

@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def main(member: Member):
    await add_talk(str(member.id))


@channel.use(SchedulerSchema(crontabify("0 4 * * *")))
async def reset(app: GraiaMiraiApplication):
    await reset_sign()
    await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create("签到重置成功"))