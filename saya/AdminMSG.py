import time
import random
import asyncio

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.exception import UnknownTarget
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.model import Friend, MemberInfo, Group
from graia.ariadne.message.parser.literature import Literature
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import GroupMessage, FriendMessage
from graia.ariadne.message.element import Plain, Source, Quote, At, Image

from util.text2image import create_image
from util.control import Rest, Permission
from database.db import add_gold, give_all_gold
from util.sendMessage import safeSendGroupMessage
from config import save_config, yaml_data, group_list, user_black_list

from .AdminConfig import funcList

saya = Saya.current()
channel = Channel.current()
funcList = funcList


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Literature("1", allow_quote=True, skip_one_at_in_quote=True)
        ],
        decorators=[Permission.require(Permission.MASTER)],
    )
)
async def get_botQueue(app: Ariadne, message: MessageChain, source: Source):
    print(1)
    if message.has(Quote):
        messageid = message.getFirst(Quote).id
        await app.recallMessage(messageid)
        await app.recallMessage(source)


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage], inline_dispatchers=[Literature("全员充值")]
    )
)
async def all_recharge(app: Ariadne, friend: Friend, message: MessageChain):
    Permission.manual(friend, Permission.MASTER)
    saying = message.asDisplay().split()
    await give_all_gold(int(saying[1]))
    await app.sendFriendMessage(
        friend, MessageChain.create([Plain(f"已向所有人充值 {saying[1]} 个游戏币")])
    )


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage], inline_dispatchers=[Literature("充值")]
    )
)
async def echarge(app: Ariadne, friend: Friend, message: MessageChain):
    Permission.manual(friend, Permission.MASTER)
    saying = message.asDisplay().split()
    await add_gold(saying[1], int(saying[2]))
    await app.sendFriendMessage(
        friend, MessageChain.create([Plain(f"已向 {saying[1]} 充值 {saying[2]} 个游戏币")])
    )


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage], inline_dispatchers=[Literature("公告")]
    )
)
async def Announcement(app: Ariadne, friend: Friend, message: MessageChain):
    Permission.manual(friend, Permission.MASTER)
    ft = time.time()
    saying = message.asDisplay().split(" ", 1)
    if len(saying) == 2:
        image = await create_image(saying[1])
        groupList = await app.getGroupList()
        for group in groupList:
            if group.id not in [885355617, 780537426, 474769367, 690211045, 855895642]:
                try:
                    await safeSendGroupMessage(
                        group.id,
                        MessageChain.create(
                            [Plain(f"公告：{str(group.name)}\n"), Image(data_bytes=image)]
                        ),
                    )
                except Exception as err:
                    await app.sendFriendMessage(
                        yaml_data["Basic"]["Permission"]["Master"],
                        MessageChain.create([Plain(f"{group.id} 的公告发送失败\n{err}")]),
                    )
                await asyncio.sleep(random.uniform(1, 3))
        tt = time.time()
        times = str(tt - ft)
        await app.sendFriendMessage(
            friend, MessageChain.create([Plain(f"群发已完成，耗时 {times} 秒")])
        )


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage], inline_dispatchers=[Literature("添加", "群白名单")]
    )
)
async def add_white_group(app: Ariadne, friend: Friend, message: MessageChain):
    Permission.manual(friend, Permission.MASTER)
    saying = message.asDisplay().split()
    if len(saying) == 3:
        if int(saying[2]) in group_list["white"]:
            await app.sendFriendMessage(
                friend, MessageChain.create([Plain("该群已在白名单中")])
            )
        else:
            group_list["white"].append(int(saying[2]))
            save_config()
            await app.sendFriendMessage(
                friend, MessageChain.create([Plain("成功将该群加入白名单")])
            )
    else:
        await app.sendFriendMessage(friend, MessageChain.create([Plain("未输入群号")]))


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage], inline_dispatchers=[Literature("取消", "群白名单")]
    )
)
async def remove_white_group(app: Ariadne, friend: Friend, message: MessageChain):
    Permission.manual(friend, Permission.MASTER)
    saying = message.asDisplay().split()
    if len(saying) == 3:
        if int(saying[2]) not in group_list["white"]:
            try:
                await app.quitGroup(int(saying[2]))
                await app.sendFriendMessage(
                    friend, MessageChain.create([Plain("该群未在白名单中，但成功退出")])
                )
            except Exception:
                await app.sendFriendMessage(
                    friend, MessageChain.create([Plain("该群未在白名单中，且退出失败")])
                )
        else:
            group_list["white"].remove(int(saying[2]))
            save_config()
            try:
                await safeSendGroupMessage(
                    int(saying[2]), MessageChain.create([Plain("该群已被移出白名单，将在3秒后退出")])
                )
                await asyncio.sleep(3)
                await app.quitGroup(int(saying[2]))
            except UnknownTarget:
                pass
            await app.sendFriendMessage(
                friend, MessageChain.create([Plain("成功将该群移出白名单")])
            )
    else:
        await app.sendFriendMessage(friend, MessageChain.create([Plain("未输入群号")]))


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage], inline_dispatchers=[Literature("拉黑", "用户")]
    )
)
async def fadd_black_user(app: Ariadne, friend: Friend, message: MessageChain):
    Permission.manual(friend, Permission.MASTER)
    saying = message.asDisplay().split()
    if len(saying) == 3:
        if int(saying[2]) in user_black_list:
            await app.sendFriendMessage(
                friend, MessageChain.create([Plain("该用户已在黑名单中")])
            )
        else:
            user_black_list.append(int(saying[2]))
            save_config()
            await app.sendFriendMessage(
                friend, MessageChain.create([Plain("成功将该用户加入黑名单")])
            )
    else:
        await app.sendFriendMessage(friend, MessageChain.create([Plain("未输入qq号")]))


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage], inline_dispatchers=[Literature("取消拉黑", "用户")]
    )
)
async def fremove_block_user(app: Ariadne, friend: Friend, message: MessageChain):
    Permission.manual(friend, Permission.MASTER)
    saying = message.asDisplay().split()
    if len(saying) == 3:
        if int(saying[2]) not in user_black_list:
            await app.sendFriendMessage(
                friend, MessageChain.create([Plain("该用户未在黑名单中")])
            )
        else:
            user_black_list.remove(int(saying[2]))
            save_config()
            await app.sendFriendMessage(
                friend, MessageChain.create([Plain("成功将该用户移出白名单")])
            )
    else:
        await app.sendFriendMessage(friend, MessageChain.create([Plain("未输入qq号")]))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Literature("拉黑", "用户")],
        decorators=[Permission.require(Permission.MASTER)],
    )
)
async def gadd_black_user(group: Group, message: MessageChain):
    if message.has(At):
        user = message.getFirst(At).target
        if user in user_black_list:
            await safeSendGroupMessage(
                group, MessageChain.create([At(user), Plain(" 已在黑名单中")])
            )
        else:
            user_black_list.append(user)
            save_config()
            await safeSendGroupMessage(
                group, MessageChain.create([Plain("成功将 "), At(user), Plain(" 加入黑名单")])
            )
    else:
        saying = message.asDisplay().split()
        if len(saying) == 3:
            if int(saying[2]) in user_black_list:
                await safeSendGroupMessage(
                    group, MessageChain.create([Plain("该用户已在黑名单中")])
                )
            else:
                user_black_list.append(int(saying[2]))
                save_config()
                await safeSendGroupMessage(
                    group, MessageChain.create([Plain("成功将该用户加入黑名单")])
                )
        else:
            await safeSendGroupMessage(group, MessageChain.create([Plain("未输入qq号")]))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Literature("取消拉黑", "用户")],
        decorators=[Permission.require(Permission.MASTER)],
    )
)
async def gremove_block_user(group: Group, message: MessageChain):
    if message.has(At):
        user = message.getFirst(At).target
        if user not in user_black_list:
            await safeSendGroupMessage(
                group, MessageChain.create([Plain(f"{user} 未在黑名单中")])
            )
        else:
            user_black_list.remove(user)
            save_config()
            await safeSendGroupMessage(
                group, MessageChain.create([Plain("成功将 "), At(user), Plain(" 移出黑名单")])
            )
    else:
        await safeSendGroupMessage(group, MessageChain.create([Plain("请at要操作的用户")]))


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage], inline_dispatchers=[Literature("休息")]
    )
)
async def fset_work(app: Ariadne, friend: Friend):
    Permission.manual(friend, Permission.MASTER)
    Rest.set_sleep(1)
    await app.sendFriendMessage(friend, MessageChain.create([Plain("已进入休息")]))


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage], inline_dispatchers=[Literature("工作")]
    )
)
async def fset_rest(app: Ariadne, friend: Friend):
    Permission.manual(friend, Permission.MASTER)
    Rest.set_sleep(0)
    await app.sendFriendMessage(friend, MessageChain.create([Plain("已开始工作")]))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Literature("休息")],
        decorators=[Permission.require(Permission.MASTER)],
    )
)
async def gset_work(group: Group):
    Rest.set_sleep(1)
    await safeSendGroupMessage(group, MessageChain.create([Plain("已进入休息")]))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Literature("工作")],
        decorators=[Permission.require(Permission.MASTER)],
    )
)
async def gset_rest(group: Group):
    Rest.set_sleep(0)
    await safeSendGroupMessage(group, MessageChain.create([Plain("已开始工作")]))


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage], inline_dispatchers=[Literature("群名片修正")]
    )
)
async def group_card_fix(app: Ariadne, friend: Friend):
    Permission.manual(friend, Permission.MASTER)
    grouplits = await app.getGroupList()
    i = 0
    for group in grouplits:
        opt = await app.modifyMemberInfo(
            member=yaml_data["Basic"]["MAH"]["BotQQ"],
            info=MemberInfo(name=yaml_data["Basic"]["BotName"]),
            group=group.id,
        )
        if opt is None:
            i += 1
        else:
            await app.sendFriendMessage(
                friend,
                MessageChain.create(
                    [Plain(f"群 {group.name}（{group.id}）名片修改失败，请检查后重试")]
                ),
            )
            break
        await asyncio.sleep(0.1)
    await app.sendFriendMessage(
        friend, MessageChain.create([Plain(f"共完成 {i} 个群的名片修改。")])
    )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Literature("全局关闭")],
        decorators=[Permission.require(Permission.MASTER)],
    )
)
async def gset_close(group: Group, message: MessageChain):

    func_List = funcList.copy()

    saying = message.asDisplay().split()
    if len(saying) == 2:
        sayfunc = func_List[int(saying[1]) - 1]
        if yaml_data["Saya"][sayfunc["key"]]["Disabled"]:
            return await safeSendGroupMessage(
                group, MessageChain.create([Plain(f"{sayfunc['name']} 已处于全局关闭状态")])
            )
        else:
            yaml_data["Saya"][sayfunc["key"]]["Disabled"] = True
            save_config()
            return await safeSendGroupMessage(
                group, MessageChain.create([Plain(f"{sayfunc['name']} 已全局关闭")])
            )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Literature("全局开启")],
        decorators=[Permission.require(Permission.MASTER)],
    )
)
async def gset_open(group: Group, message: MessageChain):

    func_List = funcList.copy()

    saying = message.asDisplay().split()
    if len(saying) == 2:
        sayfunc = func_List[int(saying[1]) - 1]
        if not yaml_data["Saya"][sayfunc["key"]]["Disabled"]:
            return await safeSendGroupMessage(
                group, MessageChain.create([Plain(f"{sayfunc['name']} 已处于全局开启状态")])
            )
        else:
            yaml_data["Saya"][sayfunc["key"]]["Disabled"] = False
            save_config()
            return await safeSendGroupMessage(
                group, MessageChain.create([Plain(f"{sayfunc['name']} 已全局开启")])
            )
