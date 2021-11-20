import time
import httpx
import asyncio

from io import BytesIO
from loguru import logger
from typing import Optional
from PIL import Image as IMG
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.broadcast.interrupt.waiter import Waiter
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import FriendMessage
from graia.broadcast.interrupt import InterruptControl
from graia.ariadne.model import Group, Friend, MemberInfo
from graia.ariadne.message.element import At, Plain, Image
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.lifecycle import ApplicationLaunched, ApplicationShutdowned
from graia.ariadne.event.mirai import (
    NewFriendRequestEvent,
    BotInvitedJoinGroupRequestEvent,
    BotJoinGroupEvent,
    BotLeaveEventKick,
    BotGroupPermissionChangeEvent,
    BotMuteEvent,
    MemberCardChangeEvent,
    MemberJoinEvent,
    MemberLeaveEventKick,
    MemberLeaveEventQuit,
)

from util.control import Rest
from util.TextModeration import text_moderation_async
from util.sendMessage import safeSendGroupMessage
from config import save_config, yaml_data, group_data, group_list

from .AdminConfig import groupInitData

saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
inc = InterruptControl(bcc)


@channel.use(ListenerSchema(listening_events=[ApplicationLaunched]))
async def groupDataInit(app: Ariadne):
    """
    Graia 成功启动
    """
    groupList = await app.getGroupList()
    groupNum = len(groupList)
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
    for qq in yaml_data["Basic"]["Permission"]["Admin"]:
        await app.sendFriendMessage(
            qq,
            MessageChain.create(
                [
                    Plain("收到添加好友事件"),
                    Plain(f"\nQQ：{events.supplicant}"),
                    Plain(f"\n昵称：{events.nickname}"),
                    Plain(f"\n来自群：{sourceGroup}"),
                    Plain(f"\n状态：已通过申请\n\n{events.message.upper()}"),
                ]
            ),
        )
    await events.accept()


@channel.use(ListenerSchema(listening_events=[BotInvitedJoinGroupRequestEvent]))
async def accept(app: Ariadne, invite: BotInvitedJoinGroupRequestEvent):
    """
    被邀请入群
    """
    if invite.groupId in group_list["white"]:
        await app.sendFriendMessage(
            yaml_data["Basic"]["Permission"]["Master"],
            MessageChain.create(
                [
                    Plain("收到邀请入群事件"),
                    Plain(f"\n邀请者：{invite.supplicant} | {invite.nickname}"),
                    Plain(f"\n群号：{invite.groupId}"),
                    Plain(f"\n群名：{invite.groupName}"),
                    Plain("\n该群为白名单群，已同意加入"),
                ]
            ),
        )
        await invite.accept("")
    else:
        await app.sendFriendMessage(
            yaml_data["Basic"]["Permission"]["Master"],
            MessageChain.create(
                [
                    Plain("收到邀请入群事件"),
                    Plain(f"\n邀请者：{invite.supplicant} | {invite.nickname}"),
                    Plain(f"\n群号：{invite.groupId}"),
                    Plain(f"\n群名：{invite.groupName}"),
                    Plain("\n\n请发送“同意”或“拒绝”"),
                ]
            ),
        )

        @Waiter.create_using_function([FriendMessage])
        async def waiter(waiter_friend: Friend, waiter_message: MessageChain):
            if waiter_friend.id == yaml_data["Basic"]["Permission"]["Master"]:
                saying = waiter_message.asDisplay()
                if saying == "同意":
                    return True
                elif saying == "拒绝":
                    return False
                else:
                    await app.sendFriendMessage(
                        yaml_data["Basic"]["Permission"]["Master"],
                        MessageChain.create([Plain("请发送同意或拒绝")]),
                    )

        try:
            if await asyncio.wait_for(inc.wait(waiter), timeout=300):
                group_list["white"].append(invite.groupId)
                save_config()
                await invite.accept()
                await app.sendFriendMessage(
                    yaml_data["Basic"]["Permission"]["Master"],
                    MessageChain.create([Plain("已同意申请并加入白名单")]),
                )
            else:
                await invite.reject("主人拒绝加入该群")
                await app.sendFriendMessage(
                    yaml_data["Basic"]["Permission"]["Master"],
                    MessageChain.create([Plain("已拒绝申请")]),
                )

        except asyncio.TimeoutError:
            await invite.reject("由于主人长时间未审核，已自动拒绝")
            await app.sendFriendMessage(
                yaml_data["Basic"]["Permission"]["Master"],
                MessageChain.create([Plain("申请超时已自动拒绝")]),
            )


@channel.use(ListenerSchema(listening_events=[BotJoinGroupEvent]))
async def get_BotJoinGroup(app: Ariadne, joingroup: BotJoinGroupEvent):
    """
    收到入群事件
    """
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

    if joingroup.group.id not in group_list["white"]:
        await safeSendGroupMessage(
            joingroup.group.id,
            MessageChain.create(
                f"该群未在白名单中，正在退出，如有需要请联系{yaml_data['Basic']['Permission']['Master']}申请白名单"
            ),
        )
        await app.sendFriendMessage(
            yaml_data["Basic"]["Permission"]["Master"],
            MessageChain.create("该群未在白名单中，正在退出"),
        )
        return await app.quitGroup(joingroup.group.id)

    if joingroup.group.id not in group_data:
        group_data[str(joingroup.group.id)] = groupInitData
        logger.info("已为该群初始化配置文件")
        save_config()
        await safeSendGroupMessage(
            joingroup.group.id,
            MessageChain.create(
                f"我是{yaml_data['Basic']['Permission']['MasterName']}"
                f"的机器人{yaml_data['Basic']['BotName']}，"
                f"如果有需要可以联系主人QQ”{yaml_data['Basic']['Permission']['Master']}“，"
                f"添加{yaml_data['Basic']['BotName']}好友后请私聊说明用途后即可拉进其他群，主人看到后会选择是否同意入群"
                f"\n{yaml_data['Basic']['BotName']}被群禁言后会自动退出该群。"
                "\n发送 <菜单> 可以查看功能列表"
                "\n拥有管理员以上权限可以开关功能"
                f"\n注：@{yaml_data['Basic']['BotName']}不会触发任何功能"
            ),
        )


@channel.use(ListenerSchema(listening_events=[BotLeaveEventKick]))
async def get_BotKickGroup(app: Ariadne, kickgroup: BotLeaveEventKick):
    """
    被踢出群
    """
    try:
        group_list["white"].remove(kickgroup.group.id)
    except Exception:
        pass
    save_config()

    for qq in yaml_data["Basic"]["Permission"]["Admin"]:
        await app.sendFriendMessage(
            qq,
            MessageChain.create(
                "收到被踢出群聊事件"
                f"\n群号：{kickgroup.group.id}"
                f"\n群名：{kickgroup.group.name}"
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
        group_list["white"].remove(group.id)
    except Exception:
        pass
    save_config()

    for qq in yaml_data["Basic"]["Permission"]["Admin"]:
        await app.sendFriendMessage(
            qq,
            MessageChain.create(
                [
                    Plain("收到禁言事件，已退出该群，并移出白名单"),
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
                member=yaml_data["Basic"]["MAH"]["BotQQ"],
                info=MemberInfo(name=yaml_data["Basic"]["BotName"]),
                group=events.member.group.id,
            )
            await safeSendGroupMessage(
                events.member.group.id, MessageChain.create([Plain("请不要修改我的群名片")])
            )
    else:
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
        Image(url=f"http://q1.qlogo.cn/g?b=qq&nk={str(events.member.id)}&s=4"),
        Plain(f"\n欢迎 {events.member.name} 加入本群"),
    ]
    if group_data[str(events.member.group.id)]["EventBroadcast"]["Enabled"]:
        if EventBroadcast := group_data[str(events.member.group.id)]["EventBroadcast"][
            "Message"
        ]:
            msg.append(Plain(f"\n{EventBroadcast}"))
        await safeSendGroupMessage(events.member.group, MessageChain.create(msg))


@channel.use(ListenerSchema(listening_events=[MemberLeaveEventKick]))
async def getMemberLeaveEventKick(events: MemberLeaveEventKick):
    """
    有人被踢出群聊
    """

    msg = [
        Image(data_bytes=await avater_blackandwhite(events.member.id)),
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
        Image(data_bytes=await avater_blackandwhite(events.member.id)),
        Plain(f"\n{events.member.name} 退出本群"),
    ]
    if group_data[str(events.member.group.id)]["EventBroadcast"]["Enabled"]:
        await safeSendGroupMessage(events.member.group, MessageChain.create(msg))


async def avater_blackandwhite(qq: int) -> bytes:
    """
    获取群成员头像黑白化
    """
    url = f"http://q1.qlogo.cn/g?b=qq&nk={str(qq)}&s=4"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
    img = IMG.open(BytesIO(resp.content))
    img = img.convert("L")
    img.save(imgbio := BytesIO(), "JPEG")
    return imgbio.getvalue()
