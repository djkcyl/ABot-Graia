import json
import time
import random
import asyncio

from graia.saya import Saya, Channel
from graia.application.friend import Friend
from graia.application.group import Group, Member
from graia.broadcast.interrupt.waiter import Waiter
from graia.application import GraiaMiraiApplication
from graia.broadcast.interrupt import InterruptControl
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.parser.literature import Literature
from graia.application.event.messages import GroupMessage, FriendMessage
from graia.application.message.elements.internal import MessageChain, Source, Plain, At

from datebase.db import reduce_gold, add_gold
from config import yaml_data, group_data, sendmsg


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
        await app.sendFriendMessage(member.id, MessageChain.create([Plain(f"本消息仅用于测试私信是否可用，无需回复\n{time.time()}")]))
    except:
        await app.sendGroupMessage(group, MessageChain.create([Plain(f"由于由于未添加好友，暂时无法发起你画我猜，请自行添加 {yaml_data['Basic']['BotName']} 好友，用于发送题目")]))
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
    async def start_game(submit_answer_group: Group, submit_answer_member: Member, submit_answer_message: MessageChain, submit_answer_source: Source):
        question = GROUP_GAME_PROCESS[group.id]["question"]
        owner = GROUP_GAME_PROCESS[group.id]["owner"]
        saying = submit_answer_message.asDisplay()
        if all([submit_answer_group.id == group.id,
                submit_answer_member.id != owner,
                saying == question, ]):
            return [submit_answer_member, submit_answer_source]
    # 如果当前群有一个正在进行中的游戏
    if group.id in GROUP_RUNING_LIST:
        owner = GROUP_GAME_PROCESS[group.id]["owner"]
        owner_name = (await app.getMember(group, owner)).name
        await app.sendGroupMessage(group, MessageChain.create([
            At(member.id),
            Plain(" 本群存在一场已经开始的游戏，请等待当前游戏结束"),
            Plain(f"\n发起者：{str(owner)} | {owner_name}")
        ]),
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
                    question_len = len(question)
                    await app.sendGroupMessage(group, MessageChain.create([At(member.id), Plain(f" 已确认，你成功在本群开启你画我猜，正在向你发送题目。。。如无法接收题目请自行添加 {yaml_data['Basic']['BotName']} 好友")]), quote=source)
                    await asyncio.sleep(1)
                    await app.sendGroupMessage(group, MessageChain.create([Plain(f"本次题目为 {question_len} 个字，请等待 "),
                                                                           At(member.id),
                                                                           Plain(" 在群中绘图，本次游戏将在180秒后结束")]))
                    await asyncio.sleep(1)
                    await app.sendFriendMessage(member.id, MessageChain.create([Plain(f"本次的题目为：{question}，请在一分钟内\n在群中\n在群中\n在群中\n发送涂鸦或其他形式等来表示该主题")]))
                    await asyncio.sleep(1)

                    try:
                        result = await asyncio.wait_for(inc.wait(start_game), timeout=180)
                        owner = owner = str(GROUP_GAME_PROCESS[group.id]["owner"])
                        await add_gold(owner, 2)
                        await add_gold(str(result[0].id), 2)
                        GROUP_RUNING_LIST.remove(group.id)
                        del GROUP_GAME_PROCESS[group.id]
                        await app.sendGroupMessage(group.id, MessageChain.create([
                            Plain("恭喜 "),
                            At(result[0].id),
                            Plain(f" 成功猜出本次答案，你和创建者分别获得 1 个和 2 个游戏币，本次游戏结束")
                        ]),
                            quote=result[1])
                    except asyncio.TimeoutError:
                        owner = str(GROUP_GAME_PROCESS[group.id]["owner"])
                        await add_gold(owner, 1)
                        GROUP_RUNING_LIST.remove(group.id)
                        del GROUP_GAME_PROCESS[group.id]
                        await app.sendGroupMessage(group, MessageChain.create([Plain("由于长时间没有人回答出正确答案，将返还创建者 1 个游戏币，本次你画我猜已结束")]))
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
        if saying[1] not in WORD["word"]:
            word_list = WORD["word"]
            word_list.append(saying[1])
            WORD["word"] = word_list
            with open("./saya/DrawSomething/word.json", "w") as f:
                json.dump(WORD, f, indent=2, ensure_ascii=False)
            await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([Plain(f"成功添加你画我猜词库：{saying[1]}")]))
        else:
            await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([Plain(f"词库内已存在该词")]))


@channel.use(ListenerSchema(listening_events=[FriendMessage], inline_dispatchers=[Literature("查看你画我猜状态")]))
async def main(app: GraiaMiraiApplication, friend: Friend):
    if friend.id == yaml_data['Basic']['Permission']['Master']:
        global GROUP_RUNING_LIST
        runlist_len = len(GROUP_RUNING_LIST)
        if runlist_len > 0:
            await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
                Plain(f"当前共有 {runlist_len} 个群正在玩你画我猜")
            ]))
        else:
            await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([Plain(f"当前没有正在运行你画我猜的群")]))
