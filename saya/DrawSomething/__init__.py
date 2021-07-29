import json
import random

from graia.application import GraiaMiraiApplication
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.event.messages import *
from graia.application.event.mirai import *
from graia.application.message.elements.internal import *
from graia.application.message.parser.literature import Literature
from graia.broadcast.interrupt import InterruptControl
from graia.broadcast.interrupt.waiter import Waiter

from config import yaml_data, group_data, sendmsg
from datebase.db import reduce_gold, add_gold

saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
inc = InterruptControl(bcc)

with open("./saya/DrawSomething/word.json", "r") as f:
    WORD = json.load(f)
MEMBER_RUNING_LIST = []
GROUP_RUNING_LIST = []
GROUP_GAME_PROCESS = {}


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("你画我猜")]))
async def main(app: GraiaMiraiApplication, group: Group, member: Member, source: Source):
    
    if yaml_data['Saya']['Entertainment']['Disabled']:
        return await sendmsg(app=app, group=group)
    elif 'Entertainment' in group_data[group.id]['DisabledFunc']:
        return await sendmsg(app=app, group=group)
    
    if member.id in MEMBER_RUNING_LIST:
        return
    try:
        await app.sendTempMessage(group, member, MessageChain.create([Plain("本消息仅用于测试私信是否可用，无需回复")]))
    except:
        await app.sendGroupMessage(group, MessageChain.create([Plain("由于本群设置无法发起临时会话，暂时无法发起你画我猜")]))
        return
    MEMBER_RUNING_LIST.append(member.id)
    # 请求确认中断
    @Waiter.create_using_function([GroupMessage])
    async def confirm(confirm_group: Group, confirm_member: Member, confirm_message: MessageChain, confirm_source: Source):
        if all([confirm_group.id == group.id,
                confirm_member.id == member.id]):
            saying = confirm_message.asDisplay()
            if saying == "是":
                return True
            elif saying == "否":
                return False
            else:
                await app.sendGroupMessage(group, MessageChain.create([At(confirm_member.id), Plain("请发送是或否来进行确认")]),
                                           quote=confirm_source)
    # 等待答案中断
    @Waiter.create_using_function([GroupMessage])
    async def start_game(submit_answer_group: Group, submit_answer_member: Member, submit_answer_message: MessageChain):
        question = GROUP_GAME_PROCESS[group.id]["question"]
        owner = GROUP_GAME_PROCESS[group.id]["owner"]
        saying = submit_answer_message.asDisplay()
        if all([submit_answer_group.id == group.id,
                submit_answer_member.id != owner,
                saying == question, ]):
            return submit_answer_member
    # 如果当前群有一个正在进行中的游戏
    if group.id in GROUP_RUNING_LIST:
        owner = GROUP_GAME_PROCESS[group.id]["owner"]
        owner_name = (await app.getMember(group, owner)).name
        await app.sendGroupMessage(group, MessageChain.create([At(member.id),
                                                               Plain(" 本群存在一场已经开始的游戏，请等待当前游戏结束"),
                                                               Plain(f"\n发起者：{str(owner)} | {owner_name}")]),
                                   quote=source)
        
    # 新游戏创建流程
    else:
        GROUP_RUNING_LIST.append(group.id)
        question = random.choice(WORD["word"])
        GROUP_GAME_PROCESS[group.id] = {
            "question": question,
            "owner": member.id,
        }
        await app.sendGroupMessage(group, MessageChain.create([Plain("是否确认在本群开启一场你画我猜？这将消耗你 4 个游戏币")]),
                                   quote=source)
        try:
            # 新游戏创建完成，进入等待玩家阶段
            if await asyncio.wait_for(inc.wait(confirm), timeout=10):
                if not await reduce_gold(str(member.id), 4):
                    GROUP_RUNING_LIST.remove(group.id)
                    del GROUP_GAME_PROCESS[group.id]
                    await app.sendGroupMessage(group, MessageChain.create([At(member.id), Plain(" 你的游戏币不足，无法开始游戏")]))
                else:
                    await app.sendGroupMessage(group, MessageChain.create([At(member.id), Plain(" 已确认，你成功在本群开启你画我猜，正在向发起者发送题目。。。请等待发起者在群中绘图，本次游戏将在120后结束")]))
                    try:
                        await app.sendTempMessage(group, member, MessageChain.create([Plain(f"本次的题目为：{question}，请在一分钟内在群中 在群中 在群中发送涂鸦等来表示该主题")]))
                    except:
                        GROUP_RUNING_LIST.remove(group.id)
                        del GROUP_GAME_PROCESS[group.id]
                        await add_gold(str(member.id), 4)
                        await app.sendGroupMessage(group, MessageChain.create([Plain("由于本群设置无法发起临时会话，暂时无法发起你画我猜")]))
                        return
                    
                    try:
                        result = await asyncio.wait_for(inc.wait(start_game), timeout=120)
                        owner = owner = str(GROUP_GAME_PROCESS[group.id]["owner"])
                        await add_gold(owner, 2)
                        await add_gold(str(result.id), 2)
                        GROUP_RUNING_LIST.remove(group.id)
                        del GROUP_GAME_PROCESS[group.id]
                        await app.sendGroupMessage(group.id, MessageChain.create([
                            Plain("恭喜 "),
                            At(result.id),
                            Plain(f" 成功猜出本次答案，你和创建者一起已获得 2 个游戏币，本次游戏结束")
                        ]))
                    except asyncio.TimeoutError:
                        owner = str(GROUP_GAME_PROCESS[group.id]["owner"])
                        await add_gold(owner, 2)
                        GROUP_RUNING_LIST.remove(group.id)
                        del GROUP_GAME_PROCESS[group.id]
                        await app.sendGroupMessage(group, MessageChain.create([Plain("由于长时间没有人回答出正确答案，本次你画我猜已结束")]))
            # 终止创建流程
            else:
                GROUP_RUNING_LIST.remove(group.id)
                del GROUP_GAME_PROCESS[group.id]
                await app.sendGroupMessage(group, MessageChain.create([Plain("已取消")]))
        # 如果 10 秒内无响应
        except asyncio.TimeoutError:
            GROUP_RUNING_LIST.remove(group.id)
            del GROUP_GAME_PROCESS[group.id]
            await app.sendGroupMessage(group, MessageChain.create([Plain("确认超时")]))

    MEMBER_RUNING_LIST.remove(member.id)


@channel.use(ListenerSchema(listening_events=[FriendMessage], inline_dispatchers=[Literature("添加你画我猜词库")]))
async def main(app: GraiaMiraiApplication, friend: Friend, message: MessageChain):
    if friend.id == yaml_data['Basic']['Permission']['Master']:
        global WORD
        saying = message.asDisplay().split()
        word_list = WORD["word"]
        word_list.append(saying[1])
        WORD["word"] = word_list
        with open("./saya/DrawSomething/word.json", "w") as f:
            json.dump(WORD, f, indent=2, ensure_ascii=False)
        await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([Plain(f"成功添加你画我猜词库：{saying[1]}")]))