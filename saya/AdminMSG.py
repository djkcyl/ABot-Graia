import time
import random
import asyncio

from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.exception import UnknownTarget
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.model import Friend, MemberInfo, Group
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import GroupMessage, FriendMessage
from graia.ariadne.message.element import Plain, Source, Quote, At, Image
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    RegexResult,
    ElementMatch,
    ElementResult,
    WildcardMatch,
)

from util.text2image import create_image
from database.db import add_gold, give_all_gold
from util.sendMessage import safeSendGroupMessage
from util.control import Rest, Permission, bot_shutdown
from config import (
    COIN_NAME,
    yaml_data,
    save_config,
    user_black_list,
    group_black_list,
    group_white_list,
)

from .AdminConfig import funcList

channel = Channel.current()
funcList = funcList


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("1")])],
        decorators=[Permission.require(Permission.MASTER)],
    )
)
async def get_botQueue(app: Ariadne, message: MessageChain, source: Source):
    if message.has(Quote):
        messageid = message.getFirst(Quote).id
        try:
            await app.recallMessage(messageid)
            await app.recallMessage(source)
        except PermissionError:
            pass


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage],
        inline_dispatchers=[
            Twilight([FullMatch("全员充值"), "anything" @ WildcardMatch(optional=True)])
        ],
    )
)
async def all_recharge(app: Ariadne, friend: Friend, anything: RegexResult):
    Permission.manual(friend, Permission.MASTER)
    if anything.matched:
        say = anything.result.asDisplay()
        await give_all_gold(int(say))
        await app.sendFriendMessage(
            friend, MessageChain.create(f"已向所有人充值 {say} 个{COIN_NAME}")
        )
    else:
        await app.sendFriendMessage(friend, MessageChain.create("请输入充值数量"))


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage],
        inline_dispatchers=[
            Twilight([FullMatch("充值"), "anything" @ WildcardMatch(optional=True)])
        ],
    )
)
async def echarge(app: Ariadne, friend: Friend, anything: RegexResult):
    Permission.manual(friend, Permission.MASTER)
    if anything.matched:
        saying = anything.result.asDisplay().split()
        if len(saying) == 2:
            await add_gold(saying[0], int(saying[1]))
            await app.sendFriendMessage(
                friend,
                MessageChain.create(f"已向 {saying[0]} 充值 {saying[1]} 个{COIN_NAME}"),
            )
        else:
            await app.sendFriendMessage(friend, MessageChain.create("缺少充值对象或充值数量"))
    else:
        await app.sendFriendMessage(friend, MessageChain.create("请输入充值对象和充值数量"))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([FullMatch("充值"), "anything" @ WildcardMatch(optional=True)])
        ],
        decorators=[Permission.require(Permission.MASTER)],
    )
)
async def group_echarge(group: Group, anything: RegexResult):
    if anything.matched:
        saying = anything.result.asDisplay().split()
        if anything.result.has(At):
            at = anything.result.getFirst(At).target
            await add_gold(str(at), int(saying[1]))
            await safeSendGroupMessage(
                group,
                MessageChain.create(f"已向 {at} 充值 {saying[1]} 个{COIN_NAME}"),
            )
        elif len(saying) == 2:
            await add_gold(saying[0], int(saying[1]))
            await safeSendGroupMessage(
                group,
                MessageChain.create(f"已向 {saying[0]} 充值 {saying[1]} 个{COIN_NAME}"),
            )
        else:
            await safeSendGroupMessage(group, MessageChain.create("缺少充值对象或充值数量"))
    else:
        await safeSendGroupMessage(group, MessageChain.create("请输入充值对象和充值数量"))


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage],
        inline_dispatchers=[
            Twilight([FullMatch("公告"), "anything" @ WildcardMatch(optional=True)])
        ],
    )
)
async def Announcement(app: Ariadne, friend: Friend, anything: RegexResult):
    Permission.manual(friend, Permission.MASTER)
    ft = time.time()
    if anything.matched:
        saying = anything.result.asDisplay()
        image = await create_image(saying)
        groupList = (
            [await app.getGroup(yaml_data["Basic"]["Permission"]["DebugGroup"])]
            if yaml_data["Basic"]["Permission"]["Debug"]
            else await app.getGroupList()
        )
        await app.sendFriendMessage(
            friend,
            MessageChain.create(
                [Plain(f"正在开始发送公告，共有{len(groupList)}个群"), Image(data_bytes=image)]
            ),
        )
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
                await asyncio.sleep(random.uniform(2, 4))
        tt = time.time()
        times = str(tt - ft)
        await app.sendFriendMessage(
            friend, MessageChain.create([Plain(f"群发已完成，耗时 {times} 秒")])
        )
    else:
        await app.sendFriendMessage(friend, MessageChain.create("请输入公告内容"))


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage],
        inline_dispatchers=[
            Twilight(
                [FullMatch("添加群白名单"), "groupid" @ WildcardMatch(optional=True)],
            )
        ],
    )
)
async def add_white_group(app: Ariadne, friend: Friend, groupid: RegexResult):
    Permission.manual(friend, Permission.MASTER)
    if groupid.matched:
        say = groupid.result.asDisplay()
        if say.isdigit():
            if int(say) in group_white_list:
                await app.sendFriendMessage(friend, MessageChain.create("该群已在白名单中"))
            else:
                group_white_list.append(int(say))
                save_config()
                await app.sendFriendMessage(friend, MessageChain.create("成功将该群加入白名单"))
        else:
            await app.sendFriendMessage(friend, MessageChain.create("群号仅可为数字"))
    else:
        await app.sendFriendMessage(friend, MessageChain.create("未输入群号"))


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage],
        inline_dispatchers=[
            Twilight(
                [FullMatch("移出群白名单"), "groupid" @ WildcardMatch(optional=True)],
            )
        ],
    )
)
async def remove_white_group(app: Ariadne, friend: Friend, groupid: RegexResult):
    Permission.manual(friend, Permission.MASTER)
    if groupid.matched:
        say = groupid.result.asDisplay()
        if say.isdigit():
            if int(say) not in group_white_list:
                try:
                    await app.quitGroup(int(say))
                    await app.sendFriendMessage(
                        friend, MessageChain.create("该群未在白名单中，但成功退出")
                    )
                except Exception:
                    await app.sendFriendMessage(
                        friend, MessageChain.create("该群未在白名单中，且退出失败")
                    )
            else:
                group_white_list.remove(int(say))
                save_config()
                try:
                    await safeSendGroupMessage(
                        int(say), MessageChain.create("该群已被移出白名单，将在3秒后退出")
                    )
                    await asyncio.sleep(3)
                    await app.quitGroup(int(say))
                except UnknownTarget:
                    pass
                await app.sendFriendMessage(friend, MessageChain.create("成功将该群移出白名单"))
        else:
            await app.sendFriendMessage(friend, MessageChain.create("群号仅可为数字"))
    else:
        await app.sendFriendMessage(friend, MessageChain.create("未输入群号"))


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage],
        inline_dispatchers=[
            Twilight(
                [FullMatch("拉黑用户"), "userid" @ WildcardMatch(optional=True)],
            )
        ],
    )
)
async def fadd_black_user(app: Ariadne, friend: Friend, userid: RegexResult):
    Permission.manual(friend, Permission.MASTER)
    if userid.matched:
        say = userid.result.asDisplay()
        if say.isdigit():
            if int(say) in user_black_list:
                await app.sendFriendMessage(
                    friend, MessageChain.create([Plain("该用户已在黑名单中")])
                )
            else:
                user_black_list.append(int(say))
                save_config()
                await app.sendFriendMessage(
                    friend, MessageChain.create([Plain("成功将该用户加入黑名单")])
                )
                try:
                    await app.deleteFriend(int(say))
                    await app.sendFriendMessage(
                        friend, MessageChain.create([Plain("已删除该好友")])
                    )
                except Exception as e:
                    await app.sendFriendMessage(
                        friend, MessageChain.create([Plain(f"删除好友失败 {type(e)}")])
                    )
        else:
            await app.sendFriendMessage(friend, MessageChain.create("用户号仅可为数字"))
    else:
        await app.sendFriendMessage(friend, MessageChain.create("未输入qq号"))


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage],
        inline_dispatchers=[
            Twilight(
                [FullMatch("取消拉黑用户"), "userid" @ WildcardMatch(optional=True)],
            )
        ],
    )
)
async def fremove_block_user(app: Ariadne, friend: Friend, userid: RegexResult):
    Permission.manual(friend, Permission.MASTER)
    if userid.matched:
        say = userid.result.asDisplay()
        if say.isdigit():
            if int(say) not in user_black_list:
                await app.sendFriendMessage(friend, MessageChain.create("该用户未在黑名单中"))
            else:
                user_black_list.remove(int(say))
                save_config()
                await app.sendFriendMessage(friend, MessageChain.create("成功将该用户移出白名单"))
        else:
            await app.sendFriendMessage(friend, MessageChain.create("用户号仅可为数字"))
    else:
        await app.sendFriendMessage(friend, MessageChain.create("未输入qq号"))


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage],
        inline_dispatchers=[
            Twilight(
                [
                    FullMatch("拉黑群"),
                    "groupid" @ WildcardMatch(optional=True),
                ]
            )
        ],
    )
)
async def fadd_group_black(app: Ariadne, friend: Friend, groupid: RegexResult):
    Permission.manual(friend, Permission.MASTER)
    if groupid.matched:
        say = groupid.result.asDisplay()
        if say.isdigit():
            if int(say) in group_black_list:
                await app.sendFriendMessage(friend, MessageChain.create("该群已在黑名单中"))
            else:
                group_black_list.append(int(say))
                save_config()
                await app.sendFriendMessage(friend, MessageChain.create("成功将该群加入黑名单"))
                try:
                    await app.quitGroup(int(say))
                    await app.sendFriendMessage(friend, MessageChain.create("已退出该群"))
                except Exception as e:
                    await app.sendFriendMessage(
                        friend, MessageChain.create(f"退出群失败 {type(e)}")
                    )
        else:
            await app.sendFriendMessage(friend, MessageChain.create("群号仅可为数字"))
    else:
        await app.sendFriendMessage(friend, MessageChain.create("未输入群号"))


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage],
        inline_dispatchers=[
            Twilight([FullMatch("取消拉黑群"), "groupid" @ WildcardMatch(optional=True)])
        ],
    )
)
async def fremove_group_black(app: Ariadne, friend: Friend, groupid: RegexResult):
    Permission.manual(friend, Permission.MASTER)
    if groupid.matched:
        say = groupid.result.asDisplay()
        if say.isdigit():
            if int(say) not in group_black_list:
                await app.sendFriendMessage(friend, MessageChain.create("该群未在黑名单中"))
            else:
                group_black_list.remove(int(say))
                save_config()
                await app.sendFriendMessage(friend, MessageChain.create("成功将该群移出黑名单"))
        else:
            await app.sendFriendMessage(friend, MessageChain.create("群号仅可为数字"))
    else:
        await app.sendFriendMessage(friend, MessageChain.create("未输入群号"))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [FullMatch("拉黑用户"), "at" @ ElementMatch(At, optional=True)],
            )
        ],
        decorators=[Permission.require(Permission.MASTER)],
    )
)
async def gadd_black_user(app: Ariadne, group: Group, at: ElementResult):
    if at.matched:
        user = at.result.target
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
            try:
                await app.deleteFriend(user)
                await safeSendGroupMessage(group, MessageChain.create("已删除该好友"))
            except Exception as e:
                await safeSendGroupMessage(
                    group, MessageChain.create(f"删除好友失败 {type(e)}")
                )
    else:
        await safeSendGroupMessage(group, MessageChain.create("未输入qq号"))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [FullMatch("取消拉黑用户"), "at" @ ElementMatch(At, optional=True)],
            )
        ],
        decorators=[Permission.require(Permission.MASTER)],
    )
)
async def gremove_block_user(group: Group, at: ElementResult):
    if at.matched:
        user = at.result.target
        if user not in user_black_list:
            await safeSendGroupMessage(group, MessageChain.create(f"{user} 未在黑名单中"))
        else:
            user_black_list.remove(user)
            save_config()
            await safeSendGroupMessage(
                group, MessageChain.create([Plain("成功将 "), At(user), Plain(" 移出黑名单")])
            )
    else:
        await safeSendGroupMessage(group, MessageChain.create("请at要操作的用户"))


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage],
        inline_dispatchers=[Twilight([FullMatch("休息")])],
    )
)
async def fset_work(app: Ariadne, friend: Friend):
    Permission.manual(friend, Permission.MASTER)
    Rest.set_sleep(1)
    await app.sendFriendMessage(friend, MessageChain.create([Plain("已进入休息")]))


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage],
        inline_dispatchers=[Twilight([FullMatch("工作")])],
    )
)
async def fset_rest(app: Ariadne, friend: Friend):
    Permission.manual(friend, Permission.MASTER)
    Rest.set_sleep(0)
    await app.sendFriendMessage(friend, MessageChain.create([Plain("已开始工作")]))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("休息")])],
        decorators=[Permission.require(Permission.MASTER)],
    )
)
async def gset_work(group: Group):
    Rest.set_sleep(1)
    await safeSendGroupMessage(group, MessageChain.create([Plain("已进入休息")]))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("工作")])],
        decorators=[Permission.require(Permission.MASTER)],
    )
)
async def gset_rest(group: Group):
    Rest.set_sleep(0)
    await safeSendGroupMessage(group, MessageChain.create([Plain("已开始工作")]))


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage],
        inline_dispatchers=[Twilight([FullMatch("开机")])],
    )
)
async def fpw_on(app: Ariadne, friend: Friend):
    Permission.manual(friend, Permission.MASTER)
    bot_shutdown(False)
    await app.sendFriendMessage(friend, MessageChain.create([Plain("已开机")]))


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage],
        inline_dispatchers=[Twilight([FullMatch("关机")])],
    )
)
async def fpw_off(app: Ariadne, friend: Friend):
    Permission.manual(friend, Permission.MASTER)
    bot_shutdown(True)
    await app.sendFriendMessage(friend, MessageChain.create([Plain("已关机")]))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("关机")])],
        decorators=[Permission.require(Permission.MASTER)],
    )
)
async def gpw_off(group: Group):
    bot_shutdown(True)
    await safeSendGroupMessage(group, MessageChain.create([Plain("已关机")]))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("开机")])],
        decorators=[Permission.require(Permission.MASTER)],
    )
)
async def gpw_on(group: Group):
    bot_shutdown(False)
    await safeSendGroupMessage(group, MessageChain.create([Plain("已开机")]))


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage],
        inline_dispatchers=[Twilight([FullMatch("群名片修正")])],
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
                MessageChain.create([Plain(f"群 {group.name}（{group.id}）名片修改失败，请检查后重试")]),
            )
            await asyncio.sleep(0.5)
            break
    await app.sendFriendMessage(friend, MessageChain.create([Plain(f"共完成 {i} 个群的名片修改。")]))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([FullMatch("全局关闭"), "func" @ WildcardMatch(optional=True)])
        ],
        decorators=[Permission.require(Permission.MASTER)],
    )
)
async def gset_close(group: Group, func: RegexResult):

    func_List = funcList.copy()

    if func.matched:
        say = func.result.asDisplay()
        if say.isdigit():
            try:
                sayfunc = func_List[int(say) - 1]
            except IndexError:
                await safeSendGroupMessage(group, MessageChain.create(f"{say} 不存在"))
            else:
                if yaml_data["Saya"][sayfunc["key"]]["Disabled"]:
                    await safeSendGroupMessage(
                        group, MessageChain.create(f"{sayfunc['name']} 已处于全局关闭状态")
                    )
                else:
                    yaml_data["Saya"][sayfunc["key"]]["Disabled"] = True
                    save_config()
                    await safeSendGroupMessage(
                        group, MessageChain.create(f"{sayfunc['name']} 已全局关闭")
                    )
        else:
            await safeSendGroupMessage(group, MessageChain.create("功能编号仅可为数字"))
    else:
        await safeSendGroupMessage(group, MessageChain.create("请输入功能编号"))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([FullMatch("全局开启"), "func" @ WildcardMatch(optional=True)])
        ],
        decorators=[Permission.require(Permission.MASTER)],
    )
)
async def gset_open(group: Group, func: RegexResult):

    func_List = funcList.copy()

    if func.matched:
        say = func.result.asDisplay()
        if say.isdigit():
            try:
                sayfunc = func_List[int(say) - 1]
            except IndexError:
                await safeSendGroupMessage(group, MessageChain.create(f"{say} 不存在"))
            else:
                if not yaml_data["Saya"][sayfunc["key"]]["Disabled"]:
                    return await safeSendGroupMessage(
                        group,
                        MessageChain.create([Plain(f"{sayfunc['name']} 已处于全局开启状态")]),
                    )
                else:
                    yaml_data["Saya"][sayfunc["key"]]["Disabled"] = False
                    save_config()
                    return await safeSendGroupMessage(
                        group, MessageChain.create([Plain(f"{sayfunc['name']} 已全局开启")])
                    )
        else:
            await safeSendGroupMessage(group, MessageChain.create("功能编号仅可为数字"))
    else:
        await safeSendGroupMessage(group, MessageChain.create("请输入功能编号"))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("/quit")])],
        decorators=[Permission.require(Permission.GROUP_ADMIN)],
    )
)
async def quit_group(app: Ariadne, group: Group):
    await safeSendGroupMessage(group, MessageChain.create("正在退出群聊"))
    await app.quitGroup(group.id)
    await app.sendFriendMessage(
        yaml_data["Basic"]["Permission"]["Master"],
        MessageChain.create(f"主动退出群聊 {group.name}({group.id})"),
    )


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage],
        inline_dispatchers=[Twilight([FullMatch("发送协议")])],
    )
)
async def user_agreement(app: Ariadne, friend: Friend):
    Permission.manual(friend, Permission.MASTER)
    image = await create_image(
        "0. 本协议是 ABot（下统称“机器人”）默认服务协议。如果你看到了这句话，意味着你或你的群友应用默认协议，请注意。该协议仅会出现一次。\n"
        "1. 邀请机器人、使用机器人服务和在群内阅读此协议视为同意并承诺遵守此协议，否则请持有管理员或管理员以上权限的用户使用 /quit 移出机器人。"
        "邀请机器人入群请关闭群内每分钟消息发送限制的设置。\n"
        "2. 不允许禁言、踢出或刷屏等机器人的不友善行为，这些行为将会提高机器人被制裁的风险。开关机器人功能请持有管理员或管理员以上权限的用户使用相应的指令来进行操作。"
        "如果发生禁言、踢出等行为，机器人将拉黑该群。\n"
        "3. 机器人默认邀请行为已事先得到群内同意，因而会自动同意群邀请。因擅自邀请而使机器人遭遇不友善行为时，邀请者因未履行预见义务而将承担连带责任。\n"
        "4. 机器人在运行时将对群内信息进行监听及记录，并将这些信息保存在服务器内，以便功能正常使用。\n"
        "5. 禁止将机器人用于违法犯罪行为。\n"
        "6. 禁止使用机器人提供的功能来上传或试图上传任何可能导致的资源污染的内容，包括但不限于色情、暴力、恐怖、政治、色情、赌博等内容。如果发生该类行为，机器人将停止对该用户提供所有服务。\n"
        "6. 对于设置敏感昵称等无法预见但有可能招致言论审查的行为，机器人可能会出于自我保护而拒绝提供服务。\n"
        "7. 由于技术以及资金原因，我们无法保证机器人 100% 的时间稳定运行，可能不定时停机维护或遭遇冻结，对于该类情况恕不通知，敬请谅解。"
        "临时停机的机器人不会有任何响应，故而不会影响群内活动，此状态下仍然禁止不友善行为。\n"
        "8. 对于违反协议的行为，机器人将终止对用户和所在群提供服务，并将不良记录共享给其他服务提供方。黑名单相关事宜可以与服务提供方协商，但最终裁定权在服务提供方。\n"
        "9. 本协议内容随时有可能改动。\n"
        "10. 机器人提供的服务是完全免费的，欢迎通过其他渠道进行支持。\n"
        "11. 本服务最终解释权归服务提供方所有。",
    )
    groupList = (
        [await app.getGroup(yaml_data["Basic"]["Permission"]["DebugGroup"])]
        if yaml_data["Basic"]["Permission"]["Debug"]
        else await app.getGroupList()
    )
    await app.sendFriendMessage(
        friend,
        MessageChain.create(
            [Plain(f"正在开始发送公告，共有{len(groupList)}个群"), Image(data_bytes=image)]
        ),
    )
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
            await asyncio.sleep(random.uniform(2, 4))
