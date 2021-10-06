import json
import time
import secrets
import asyncio

from graia.saya import Saya, Channel
from graia.application.friend import Friend
from graia.application.group import Group, Member
from graia.broadcast.interrupt.waiter import Waiter
from graia.application import GraiaMiraiApplication
from graia.application.exceptions import UnknownTarget
from graia.broadcast.interrupt import InterruptControl
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.parser.literature import Literature
from graia.application.event.lifecycle import ApplicationShutdowned
from graia.application.event.messages import GroupMessage, FriendMessage
from graia.application.message.elements.internal import MessageChain, Source, Plain, At

from util.limit import group_limit_check
from util.UserBlock import group_black_list_block
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


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Literature("你画我猜")],
                            headless_decorators=[group_limit_check(20), group_black_list_block()]))
async def main(app: GraiaMiraiApplication, group: Group, member: Member, source: Source):

    # 判断插件是否处于禁用状态
    if yaml_data['Saya']['Entertainment']['Disabled']:
        return await sendmsg(app=app, group=group)
    elif 'Entertainment' in group_data[group.id]['DisabledFunc']:
        return await sendmsg(app=app, group=group)

    # 判断用户是否正在游戏中
    if member.id in MEMBER_RUNING_LIST:
        return
    else:
        MEMBER_RUNING_LIST.append(member.id)

    # 判断私信是否可用
    try:
        await app.sendFriendMessage(member.id, MessageChain.create([
            Plain(f"本消息仅用于测试私信是否可用，无需回复\n{time.time()}")
        ]))
    except:
        await app.sendGroupMessage(group, MessageChain.create([
            Plain(f"由于你未添加好友，暂时无法发起你画我猜，请自行添加 {yaml_data['Basic']['BotName']} 好友，用于发送题目")
        ]))
        MEMBER_RUNING_LIST.remove(member.id)
        return

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
                await app.sendGroupMessage(group, MessageChain.create([
                    At(confirm_member.id),
                    Plain("请发送是或否来进行确认")
                ]), quote=confirm_source)

    # 等待答案中断
    @Waiter.create_using_function([GroupMessage])
    async def start_game(submit_answer_group: Group, submit_answer_member: Member, submit_answer_message: MessageChain, submit_answer_source: Source):
        group_id = GROUP_GAME_PROCESS[group.id]
        owner = group_id["owner"]
        question = group_id["question"].upper()
        question_len = len(question)
        saying = submit_answer_message.asDisplay().upper()
        saying_len = len(saying)

        if all([submit_answer_member.id == owner, saying in ["终止", "取消", "结束"]]):
            return False

        if all([submit_answer_group.id == group.id, submit_answer_member.id != owner, saying_len == question_len]):
            if submit_answer_member.id not in group_id["player"]:
                GROUP_GAME_PROCESS[group.id]["player"][submit_answer_member.id] = 1
            if group_id["player"][submit_answer_member.id] < 9:
                talk_num = group_id["player"][submit_answer_member.id] + 1
                GROUP_GAME_PROCESS[group.id]["player"][submit_answer_member.id] = talk_num
                if saying == question:
                    return [submit_answer_member, submit_answer_source]
            elif group_id["player"][submit_answer_member.id] == 9:
                await app.sendGroupMessage(group, MessageChain.create([
                    At(submit_answer_member.id),
                    Plain("你的本回合答题机会已用尽")
                ]), quote=submit_answer_source)

    # 如果当前群有一个正在进行中的游戏
    if group.id in GROUP_RUNING_LIST:
        if group.id not in GROUP_GAME_PROCESS:
            await app.sendGroupMessage(group, MessageChain.create([
                At(member.id),
                Plain(" 本群正在请求确认开启一场游戏，请稍候")
            ]), quote=source)
        else:
            owner = GROUP_GAME_PROCESS[group.id]["owner"]
            owner_name = (await app.getMember(group, owner)).name
            await app.sendGroupMessage(group, MessageChain.create([
                At(member.id),
                Plain(" 本群存在一场已经开始的游戏，请等待当前游戏结束"),
                Plain(f"\n发起者：{str(owner)} | {owner_name}")
            ]), quote=source)

    # 新游戏创建流程
    else:
        GROUP_RUNING_LIST.append(group.id)
        try:
            await app.sendGroupMessage(group, MessageChain.create([
                Plain("是否确认在本群开启一场你画我猜？这将消耗你 4 个游戏币")
            ]), quote=source)
        except UnknownTarget:
            await app.sendGroupMessage(group, MessageChain.create([
                At(member.id),
                Plain(" 是否确认在本群开启一场你画我猜？这将消耗你 4 个游戏币")
            ]))
        try:
            # 新游戏创建完成，进入等待玩家阶段
            if await asyncio.wait_for(inc.wait(confirm), timeout=15):
                question = secrets.choice(WORD["word"])
                GROUP_GAME_PROCESS[group.id] = {
                    "question": question,
                    "owner": member.id,
                    "player": {}
                }
                if not await reduce_gold(str(member.id), 4):
                    GROUP_RUNING_LIST.remove(group.id)
                    del GROUP_GAME_PROCESS[group.id]
                    await app.sendGroupMessage(group, MessageChain.create([
                        At(member.id),
                        Plain(" 你的游戏币不足，无法开始游戏")]))
                else:
                    question_len = len(question)
                    try:
                        await app.sendGroupMessage(group, MessageChain.create([
                            Plain(f"本次题目为 {question_len} 个字，请等待 "),
                            At(member.id),
                            Plain(" 在群中绘图"),
                            Plain("\n创建者发送 <取消/终止/结束> 可结束本次游戏"),
                            Plain("\n每人每回合只有 8 次答题机会，请勿刷屏请勿抢答。")
                        ]), quote=source)
                    except UnknownTarget:
                        await app.sendGroupMessage(group, MessageChain.create([
                            Plain(f"本次题目为 {question_len} 个字，请等待 "),
                            Plain(" 在群中绘图"),
                            Plain("\n创建者发送 <取消/终止/结束> 可结束本次游戏"),
                            Plain("\n每人每回合只有 8 次答题机会，请勿刷屏请勿抢答。")
                        ]))
                    await asyncio.sleep(1)
                    await app.sendFriendMessage(member.id, MessageChain.create([
                        Plain(f"本次的题目为：{question}，请在一分钟内\n在群中\n在群中\n在群中\n发送涂鸦或其他形式等来表示该主题")
                    ]))

                    try:
                        result = await asyncio.wait_for(inc.wait(start_game), timeout=180)
                        if result:
                            owner = owner = str(GROUP_GAME_PROCESS[group.id]["owner"])
                            await add_gold(owner, 2)
                            await add_gold(str(result[0].id), 1)
                            GROUP_RUNING_LIST.remove(group.id)
                            del GROUP_GAME_PROCESS[group.id]
                            try:
                                await app.sendGroupMessage(group.id, MessageChain.create([
                                    Plain("恭喜 "),
                                    At(result[0].id),
                                    Plain(f" 成功猜出本次答案，你和创建者分别获得 1 个和 2 个游戏币，本次游戏结束")
                                ]), quote=result[1])
                            except UnknownTarget:
                                await app.sendGroupMessage(group.id, MessageChain.create([
                                    Plain("恭喜 "),
                                    At(result[0].id),
                                    Plain(f" 成功猜出本次答案，你和创建者分别获得 1 个和 2 个游戏币，本次游戏结束")
                                ]))
                        else:
                            owner = str(GROUP_GAME_PROCESS[group.id]["owner"])
                            await add_gold(owner, 1)
                            GROUP_RUNING_LIST.remove(group.id)
                            del GROUP_GAME_PROCESS[group.id]
                            await app.sendGroupMessage(group, MessageChain.create([
                                Plain("本次你画我猜已终止，将返还创建者 1 个游戏币")
                            ]))
                    except asyncio.TimeoutError:
                        owner = str(GROUP_GAME_PROCESS[group.id]["owner"])
                        question = GROUP_GAME_PROCESS[group.id]["question"]
                        await add_gold(owner, 1)
                        GROUP_RUNING_LIST.remove(group.id)
                        del GROUP_GAME_PROCESS[group.id]
                        await app.sendGroupMessage(group, MessageChain.create([
                            Plain("由于长时间没有人回答出正确答案，将返还创建者 1 个游戏币，本次你画我猜已结束"),
                            Plain(f"\n本次的答案为：{question}")
                        ]))

            # 终止创建流程
            else:
                GROUP_RUNING_LIST.remove(group.id)
                await app.sendGroupMessage(group, MessageChain.create([
                    Plain("已取消")
                ]))
        # 如果 15 秒内无响应
        except asyncio.TimeoutError:
            GROUP_RUNING_LIST.remove(group.id)
            await app.sendGroupMessage(group, MessageChain.create([
                Plain("确认超时")
            ]))

    # 将用户移除正在游戏中
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
            await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
                Plain(f"成功添加你画我猜词库：{saying[1]}")
            ]))
        else:
            await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
                Plain(f"词库内已存在该词")
            ]))


@channel.use(ListenerSchema(listening_events=[FriendMessage], inline_dispatchers=[Literature("删除你画我猜词库")]))
async def main(app: GraiaMiraiApplication, friend: Friend, message: MessageChain):
    if friend.id == yaml_data['Basic']['Permission']['Master']:
        global WORD
        saying = message.asDisplay().split()
        if saying[1] in WORD["word"]:
            word_list = WORD["word"]
            word_list.remove(saying[1])
            WORD["word"] = word_list
            with open("./saya/DrawSomething/word.json", "w") as f:
                json.dump(WORD, f, indent=2, ensure_ascii=False)
            await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
                Plain(f"成功删除你画我猜词库：{saying[1]}")
            ]))
        else:
            await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
                Plain(f"词库内未存在该词")
            ]))


@channel.use(ListenerSchema(listening_events=[FriendMessage], inline_dispatchers=[Literature("查看你画我猜状态")]))
async def main(app: GraiaMiraiApplication, friend: Friend):
    if friend.id == yaml_data['Basic']['Permission']['Master']:
        runlist_len = len(GROUP_RUNING_LIST)
        runlist_str = "\n".join(map(lambda x: str(x), GROUP_RUNING_LIST))
        if runlist_len > 0:
            await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
                Plain(f"当前共有 {runlist_len} 个群正在玩你画我猜"),
                Plain(f"\n{runlist_str}")
            ]))
        else:
            await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
                Plain(f"当前没有正在运行你画我猜的群")
            ]))


@channel.use(ListenerSchema(listening_events=[ApplicationShutdowned]))
async def groupDataInit(app: GraiaMiraiApplication):
    for game_group in GROUP_RUNING_LIST:
        if game_group in GROUP_GAME_PROCESS:
            await add_gold(str(GROUP_GAME_PROCESS[game_group]['owner']), 4)
            await app.sendGroupMessage(game_group, MessageChain.create([
                Plain(f"由于 {yaml_data['Basic']['BotName']} 正在重启，本场你画我猜重置，已补偿4个游戏币")
            ]))
            await asyncio.sleep(0.2)
