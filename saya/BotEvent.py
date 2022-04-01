import time
# import asyncio

from io import BytesIO
from loguru import logger
from typing import Optional
from PIL import Image as IMG
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import MemberInfo, Group
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At, Plain, Image
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.lifecycle import ApplicationLaunched, ApplicationShutdowned
from graia.ariadne.event.mirai import (
    BotMuteEvent,
    MemberJoinEvent,
    BotJoinGroupEvent,
    BotLeaveEventKick,
    BotLeaveEventActive,
    MemberLeaveEventKick,
    MemberLeaveEventQuit,
    NewFriendRequestEvent,
    MemberCardChangeEvent,
    MemberHonorChangeEvent,
    BotGroupPermissionChangeEvent,
    BotInvitedJoinGroupRequestEvent,
)

from util.control import Rest
from database.db import init_user
from util.text2image import create_image
from util.sendMessage import safeSendGroupMessage
from util.TextModeration import text_moderation_async
from config import save_config, yaml_data, group_data, user_black_list, group_black_list, group_white_list

from .AdminConfig import groupInitData

channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[ApplicationLaunched]))
async def groupDataInit(app: Ariadne):
    """
    Graia 成功启动
    """
    # await asyncio.sleep(1)  # 这是必须的，否则会报错
    groupList = await app.getGroupList()
    groupNum = len(groupList)
    init_user(str(yaml_data["Basic"]["Permission"]["Master"]))
    await app.sendFriendMessage(
        yaml_data["Basic"]["Permission"]["Master"],
        MessageChain.create(
            [
                Plain("ABot-Graia成功启动，正在初始化，请稍后。"),
                Plain(f"\n当前 {yaml_data['Basic']['BotName']} 共加入了 {groupNum} 个群"),
            ]
        ),
    )
    i = 0
    for group in groupList:
        if str(group.id) not in group_data:
            group_data[str(group.id)] = groupInitData
            logger.info(group_data[str(group.id)])
            logger.info(f"已为 {group.id} 进行初始化配置")
            i += 1
    save_config()
    msg = [Plain("初始化结束")]
    if i > 0:
        msg.append(Plain(f"\n已为 {i} 个群进行了初始化配置"))
    if yaml_data["Basic"]["Permission"]["Debug"]:
        debug_group = await app.getGroup(yaml_data["Basic"]["Permission"]["DebugGroup"])
        debug_msg = (
            f"{debug_group.name}（{debug_group.id}）"
            if debug_group
            else yaml_data["Basic"]["Permission"]["Debug"]
        )
        master = await app.getFriend(yaml_data["Basic"]["Permission"]["Master"])
        msg.append(
            Plain(
                f"，当前为 Debug 模式，将仅接受 {debug_msg} 群以及 {master.nickname}（{master.id}） 的消息"
            )
        )
    await app.sendFriendMessage(
        yaml_data["Basic"]["Permission"]["Master"], MessageChain.create(msg)
    )

    now_localtime = time.strftime("%H:%M:%S", time.localtime())
    if "00:00:00" < now_localtime < "07:30:00":
        Rest.set_sleep(1)
        await app.sendFriendMessage(
            yaml_data["Basic"]["Permission"]["Master"],
            MessageChain.create([Plain("当前为休息时间，已进入休息状态")]),
        )


@channel.use(ListenerSchema(listening_events=[ApplicationShutdowned]))
async def stopEvents(app: Ariadne):
    await app.sendFriendMessage(
        yaml_data["Basic"]["Permission"]["Master"], MessageChain.create([Plain("正在关闭")])
    )


@channel.use(ListenerSchema(listening_events=[NewFriendRequestEvent]))
async def get_BotNewFriend(app: Ariadne, events: NewFriendRequestEvent):
    """
    收到好友申请
    """
    sourceGroup: Optional[int] = events.sourceGroup
    if sourceGroup:
        groupname = await app.getGroup(sourceGroup)
        if groupname:
            groupname = groupname.name
        else:
            groupname = "未知"

    if yaml_data["Basic"]["Event"]["NewFriend"]:
        for qq in yaml_data["Basic"]["Permission"]["Admin"]:
            await app.sendFriendMessage(
                qq,
                MessageChain.create(
                    [
                        Plain("收到添加好友事件"),
                        Plain(f"\nQQ：{events.supplicant}"),
                        Plain(f"\n昵称：{events.nickname}"),
                        Plain(f"\n来自群：{groupname}({sourceGroup})")
                        if sourceGroup
                        else Plain("\n来自好友搜索"),
                        Plain("\n状态：已通过申请\n"),
                        Plain(events.message) if events.message else Plain("无附加信息"),
                    ]
                ),
            )
    await events.accept()


@channel.use(ListenerSchema(listening_events=[BotInvitedJoinGroupRequestEvent]))
async def accept(app: Ariadne, invite: BotInvitedJoinGroupRequestEvent):
    """
    被邀请入群
    """
    if invite.sourceGroup in group_black_list:
        await app.sendFriendMessage(
            yaml_data["Basic"]["Permission"]["Master"],
            MessageChain.create(
                [
                    Plain("收到邀请入群事件"),
                    Plain(f"\n邀请者：{invite.supplicant} | {invite.nickname}"),
                    Plain(f"\n群号：{invite.sourceGroup}"),
                    Plain(f"\n群名：{invite.groupName}"),
                    Plain("\n该群为黑名单群，已拒绝加入"),
                ]
            ),
        )
        await invite.reject("该群已被拉黑")
    else:
        await app.sendFriendMessage(
            invite.supplicant,
            MessageChain.create(
                Image(
                    data_bytes=await create_image(
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
                )
            ),
        )
        await app.sendFriendMessage(
            yaml_data["Basic"]["Permission"]["Master"],
            MessageChain.create(
                [
                    Plain("收到邀请入群事件"),
                    Plain(f"\n邀请者：{invite.supplicant} | {invite.nickname}"),
                    Plain(f"\n群号：{invite.sourceGroup}"),
                    Plain(f"\n群名：{invite.groupName}"),
                ]
            ),
        )

        if yaml_data["Basic"]["Permission"]["DefaultAcceptInvite"]:
            await invite.accept()
            await app.sendFriendMessage(
                yaml_data["Basic"]["Permission"]["Master"],
                MessageChain.create([Plain("已同意申请")]),
            )
        else:
            await invite.reject("由于主人未开启群自动审核，已自动拒绝")
            await app.sendFriendMessage(
                yaml_data["Basic"]["Permission"]["Master"],
                MessageChain.create([Plain("已拒绝申请")]),
            )


@channel.use(ListenerSchema(listening_events=[BotJoinGroupEvent]))
async def get_BotJoinGroup(app: Ariadne, joingroup: BotJoinGroupEvent):
    """
    收到入群事件
    """
    if str(joingroup.group.id) not in group_data:
        group_data[str(joingroup.group.id)] = groupInitData
        logger.info("已为该群初始化配置文件")
        save_config()

    if joingroup.group.id in group_black_list:
        await safeSendGroupMessage(
            joingroup.group.id,
            MessageChain.create("该群已被拉黑，正在退出"),
        )
        await app.sendFriendMessage(
            yaml_data["Basic"]["Permission"]["Master"],
            MessageChain.create("该群已被拉黑，正在退出"),
        )
        return await app.quitGroup(joingroup.group.id)

    if (
        joingroup.group.id not in group_white_list
        and not yaml_data["Basic"]["Permission"]["DefaultAcceptInvite"]
    ):
        await safeSendGroupMessage(
            joingroup.group.id,
            MessageChain.create(
                f"该群未在白名单中，正在退出，如有需要请联系 {yaml_data['Basic']['Permission']['Master']} 申请白名单"
            ),
        )
        await app.sendFriendMessage(
            yaml_data["Basic"]["Permission"]["Master"],
            MessageChain.create("该群未在白名单中，正在退出"),
        )
        return await app.quitGroup(joingroup.group.id)

    member_count = len(await app.getMemberList(joingroup.group))
    if member_count < 15:
        if joingroup.group.id not in group_white_list:
            await safeSendGroupMessage(
                joingroup.group.id,
                MessageChain.create(f"当前群人数过少 ({member_count}/15)，暂不加入"),
            )
            await app.sendFriendMessage(
                yaml_data["Basic"]["Permission"]["Master"],
                MessageChain.create(f"该群人数过少 ({member_count})，正在退出"),
            )
            return await app.quitGroup(joingroup.group.id)

    if yaml_data["Basic"]["Event"]["JoinGroup"]:
        membernum = len(await app.getMemberList(joingroup.group))
        await app.sendFriendMessage(
            yaml_data["Basic"]["Permission"]["Master"],
            MessageChain.create(
                [
                    Plain("收到加入群聊事件"),
                    Plain(f"\n群号：{joingroup.group.id}"),
                    Plain(f"\n群名：{joingroup.group.name}"),
                    Plain(f"\n群人数：{membernum}"),
                ]
            ),
        )
    await safeSendGroupMessage(
        joingroup.group.id,
        MessageChain.create(
            f"我是 {yaml_data['Basic']['Permission']['MasterName']} "
            f"的机器人 {yaml_data['Basic']['BotName']}，"
            f"如果有需要可以联系主人QQ”{yaml_data['Basic']['Permission']['Master']}“"
            f"\n{yaml_data['Basic']['BotName']}被群禁言后会自动退出该群。"
            "\n发送 <菜单> 可以查看功能列表"
            "\n拥有管理员以上权限可以开关功能"
            f"\n注：@{yaml_data['Basic']['BotName']}不会触发任何功能"
        ),
    )
    await safeSendGroupMessage(
        joingroup.group.id,
        MessageChain.create(
            Image(
                data_bytes=await create_image(
                    "0. 本协议是 ABot（下统称“机器人”）默认服务协议。如果你看到了这句话，意味着你或你的群友应用默认协议，请注意。该协议仅会出现一次。\n"
                    "1. 邀请机器人、使用机器人服务和在群内阅读此协议视为同意并承诺遵守此协议，否则请持有管理员或管理员以上权限的用户使用 /quit 移出机器人。"
                    "邀请机器人入群请关闭群内每分钟消息发送限制的设置。\n"
                    "2. 不允许禁言、踢出或刷屏等机器人的不友善行为，这些行为将会提高机器人被制裁的风险。开关机器人功能请持有管理员或管理员以上权限的用户使用相应的指令来进行操作。"
                    "如果发生禁言、踢出等行为，机器人将拉黑该群。\n"
                    "3. 机器人默认邀请行为已事先得到群内同意，因而会自动同意群邀请。因擅自邀请而使机器人遭遇不友善行为时，邀请者因未履行预见义务而将承担连带责任。\n"
                    "4. 机器人在运行时将对群内信息进行监听及记录，并将这些信息保存在服务器内，以便功能正常使用。\n"
                    "5. 禁止将机器人用于违法犯罪行为。\n"
                    "6. 禁止使用机器人提供的功能来上传或试图上传任何可能导致的资源污染的内容，包括但不限于色情、暴力、恐怖、政治、色情、赌博等内容。"
                    "如果发生该类行为，机器人将停止对该用户提供所有服务。\n"
                    "6. 对于设置敏感昵称等无法预见但有可能招致言论审查的行为，机器人可能会出于自我保护而拒绝提供服务。\n"
                    "7. 由于技术以及资金原因，我们无法保证机器人 100% 的时间稳定运行，可能不定时停机维护或遭遇冻结，对于该类情况恕不通知，敬请谅解。"
                    "临时停机的机器人不会有任何响应，故而不会影响群内活动，此状态下仍然禁止不友善行为。\n"
                    "8. 对于违反协议的行为，机器人将终止对用户和所在群提供服务，并将不良记录共享给其他服务提供方。黑名单相关事宜可以与服务提供方协商，但最终裁定权在服务提供方。\n"
                    "9. 本协议内容随时有可能改动。\n"
                    "10. 机器人提供的服务是完全免费的，欢迎通过其他渠道进行支持。\n"
                    "11. 本服务最终解释权归服务提供方所有。",
                )
            )
        ),
    )


@channel.use(ListenerSchema(listening_events=[BotLeaveEventKick]))
async def get_BotKickGroup(app: Ariadne, kickgroup: BotLeaveEventKick):
    """
    被踢出群
    """
    try:
        group_white_list.remove(kickgroup.group.id)
    except Exception:
        pass
    try:
        group_black_list.append(kickgroup.group.id)
    except Exception:
        pass
    save_config()

    if yaml_data["Basic"]["Event"]["KickGroup"]:
        for qq in yaml_data["Basic"]["Permission"]["Admin"]:
            await app.sendFriendMessage(
                qq,
                MessageChain.create(
                    "收到被踢出群聊事件"
                    f"\n群号：{kickgroup.group.id}"
                    f"\n群名：{kickgroup.group.name}"
                    "\n已移出白名单，并加入黑名单"
                ),
            )


@channel.use(ListenerSchema(listening_events=[BotLeaveEventActive]))
async def get_BotLeaveEventActive(app: Ariadne, events: BotLeaveEventActive):
    """
    主动退群
    """
    try:
        group_white_list.remove(events.group.id)
    except Exception:
        pass
    save_config()

    if yaml_data["Basic"]["Event"]["LeaveGroup"]:
        for qq in yaml_data["Basic"]["Permission"]["Admin"]:
            await app.sendFriendMessage(
                qq,
                MessageChain.create(
                    "收到主动退出群聊事件"
                    f"\n群号：{events.group.id}"
                    f"\n群名：{events.group.name}"
                    "\n已移出白名单"
                ),
            )


@channel.use(ListenerSchema(listening_events=[BotGroupPermissionChangeEvent]))
async def get_BotPermissionChange(
    app: Ariadne, permissionchange: BotGroupPermissionChangeEvent
):
    """
    群内权限变动
    """
    if yaml_data["Basic"]["Event"]["PermissionChange"]:
        for qq in yaml_data["Basic"]["Permission"]["Admin"]:
            await app.sendFriendMessage(
                qq,
                MessageChain.create(
                    [
                        Plain("收到权限变动事件"),
                        Plain(f"\n群号：{permissionchange.group.id}"),
                        Plain(f"\n群名：{permissionchange.group.name}"),
                        Plain(f"\n权限变更为：{permissionchange.current}"),
                    ]
                ),
            )


@channel.use(ListenerSchema(listening_events=[BotMuteEvent]))
async def get_BotMuteGroup(app: Ariadne, group: Group, mute: BotMuteEvent):
    """
    被禁言
    """
    try:
        group_white_list.remove(group.id)
    except Exception:
        pass
    try:
        group_black_list.append(group.id)
    except Exception:
        pass
    try:
        user_black_list.append(mute.operator.id)
    except Exception:
        pass
    save_config()

    if yaml_data["Basic"]["Event"]["Mute"]:
        for qq in yaml_data["Basic"]["Permission"]["Admin"]:
            await app.sendFriendMessage(
                qq,
                MessageChain.create(
                    [
                        Plain("收到禁言事件，已退出该群并拉黑操作者和该群"),
                        Plain(f"\n群号：{group.id}"),
                        Plain(f"\n群名：{group.name}"),
                        Plain(f"\n操作者：{mute.operator.name} | {mute.operator.id}"),
                    ]
                ),
            )

    await app.quitGroup(group)


@channel.use(ListenerSchema(listening_events=[MemberCardChangeEvent]))
async def get_BotCardChange(app: Ariadne, events: MemberCardChangeEvent):
    """
    群名片被修改
    """
    if events.member.id == yaml_data["Basic"]["MAH"]["BotQQ"]:
        if events.current != yaml_data["Basic"]["BotName"]:
            for qq in yaml_data["Basic"]["Permission"]["Admin"]:
                await app.sendFriendMessage(
                    qq,
                    MessageChain.create(
                        [
                            Plain(f"检测到 {yaml_data['Basic']['BotName']} 群名片变动"),
                            Plain(f"\n群号：{str(events.member.group.id)}"),
                            Plain(f"\n群名：{events.member.group.name}"),
                            Plain(f"\n被修改为：{events.current}"),
                            Plain(f"\n已为你修改回：{yaml_data['Basic']['BotName']}"),
                        ]
                    ),
                )
            await app.modifyMemberInfo(
                group=events.member.group.id,
                member=yaml_data["Basic"]["MAH"]["BotQQ"],
                info=MemberInfo(name=yaml_data["Basic"]["BotName"]),
            )
            await safeSendGroupMessage(
                events.member.group.id, MessageChain.create([Plain("请不要修改我的群名片")])
            )
    elif group_data[str(events.member.group.id)]["EventBroadcast"]["Enabled"]:
        resp = await text_moderation_async(events.origin)
        resp_current = await text_moderation_async(events.current)
        if not resp["status"] and not resp_current["status"]:
            await safeSendGroupMessage(
                events.member.group,
                MessageChain.create(
                    [
                        At(events.member.id),
                        Plain(f" 的群名片由 {events.origin} 被修改为 {events.current}"),
                    ]
                ),
            )


# 群内事件
@channel.use(ListenerSchema(listening_events=[MemberJoinEvent]))
async def getMemberJoinEvent(events: MemberJoinEvent):
    """
    有人加入群聊
    """
    msg = [
        Image(data_bytes=events.member.getAvatar()),
        Plain("\n欢迎 "),
        At(events.member.id),
        Plain(" 加入本群"),
    ]
    if group_data[str(events.member.group.id)]["EventBroadcast"]["Enabled"]:
        EventBroadcast = group_data[str(events.member.group.id)]["EventBroadcast"][
            "Message"
        ]
        if EventBroadcast:
            msg.append(Plain(f"\n{EventBroadcast}"))
        await safeSendGroupMessage(events.member.group, MessageChain.create(msg))


@channel.use(ListenerSchema(listening_events=[MemberLeaveEventKick]))
async def getMemberLeaveEventKick(events: MemberLeaveEventKick):
    """
    有人被踢出群聊
    """

    msg = [
        Image(data_bytes=await avater_blackandwhite(await events.member.getAvatar(140))),
        Plain(f"\n{events.member.name} 被 "),
        At(events.operator.id),
        Plain(" 踢出本群"),
    ]
    if group_data[str(events.member.group.id)]["EventBroadcast"]["Enabled"]:
        await safeSendGroupMessage(events.member.group, MessageChain.create(msg))


@channel.use(ListenerSchema(listening_events=[MemberLeaveEventQuit]))
async def getMemberLeaveEventQuit(events: MemberLeaveEventQuit):
    """
    有人退出群聊
    """
    msg = [
        Image(data_bytes=await avater_blackandwhite(await events.member.getAvatar(140))),
        Plain(f"\n{events.member.name} 退出本群"),
    ]
    if group_data[str(events.member.group.id)]["EventBroadcast"]["Enabled"]:
        await safeSendGroupMessage(events.member.group, MessageChain.create(msg))


@channel.use(ListenerSchema(listening_events=[MemberHonorChangeEvent]))
async def get_MemberHonorChangeEvent(events: MemberHonorChangeEvent):
    """
    有人群荣誉变动
    """
    msg = [
        At(events.member.id),
        Plain(f" {'获得了' if events.action == 'achieve' else '失去了'} 群荣誉 {events.honor}！"),
    ]
    if group_data[str(events.member.group.id)]["EventBroadcast"]["Enabled"]:
        await safeSendGroupMessage(events.member.group, MessageChain.create(msg))


async def avater_blackandwhite(avatar: bytes) -> bytes:
    """
    获取群成员头像黑白化
    """
    img = IMG.open(BytesIO(avatar))
    img = img.convert("L")
    imgbio = BytesIO()
    img.save(imgbio, "JPEG")
    return imgbio.getvalue()
