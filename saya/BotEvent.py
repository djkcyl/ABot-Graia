from graia.application import GraiaMiraiApplication
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.event.messages import *
from graia.application.event.mirai import *
from graia.application.group import MemberInfo
from graia.application.message.elements.internal import *

from config import save_config, yaml_data, group_data
from .AdminConfig import groupInitData

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[NewFriendRequestEvent]))
async def get_BotJoinGroup(app: GraiaMiraiApplication, events: NewFriendRequestEvent):
    '''
    收到好友申请
    '''
    sourceGroup: Optional[int] = events.sourceGroup
    msg = "已通过申请"
    for qq in yaml_data['Basic']['Permission']['Admin']:
        await app.sendFriendMessage(qq, MessageChain.create([
            Plain("收到添加好友事件"),
            Plain(f"\nQQ：{events.supplicant}"),
            Plain(f"\n昵称：{events.nickname}"),
            Plain(f"\n来自群：{sourceGroup}"),
            Plain(f"\n状态：{msg}\n\n{events.message.upper()}")
        ]))
    await events.accept()


@channel.use(ListenerSchema(listening_events=[BotInvitedJoinGroupRequestEvent]))
async def accept(app: GraiaMiraiApplication, invite: BotInvitedJoinGroupRequestEvent):
    '''
    被邀请入群
    '''
    await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
        Plain(f"收到邀请入群事件"),
        Plain(f"\n邀请者：{invite.supplicant} | {invite.nickname}"),
        Plain(f"\n群号：{invite.groupId}"),
        Plain(f"\n群名：{invite.groupName}")
    ]))
    await invite.accept()


@channel.use(ListenerSchema(listening_events=[BotJoinGroupEvent]))
async def get_BotJoinGroup(app: GraiaMiraiApplication, joingroup: BotJoinGroupEvent):
    '''
    收到入群事件
    '''
    if joingroup.group.id not in group_data:
        group_data[joingroup.group.id] = groupInitData
        print("已为该群初始化配置文件")
        save_config()

    membernum = len(await app.memberList(joingroup.group.id))
    for qq in yaml_data['Basic']['Permission']['Admin']:
        await app.sendFriendMessage(qq, MessageChain.create([
            Plain("收到加入群聊事件"),
            Plain(f"\n群号：{joingroup.group.id}"),
            Plain(f"\n群名：{joingroup.group.name}"),
            Plain(f"\n群人数：{membernum}")
        ]))


@channel.use(ListenerSchema(listening_events=[BotLeaveEventKick]))
async def get_BotJoinGroup(app: GraiaMiraiApplication, kickgroup: BotLeaveEventKick):
    '''
    被踢出群
    '''
    for qq in yaml_data['Basic']['Permission']['Admin']:
        await app.sendFriendMessage(qq, MessageChain.create([
            Plain("收到被踢出群聊事件"),
            Plain(f"\n群号：{kickgroup.group.id}"),
            Plain(f"\n群名：{kickgroup.group.name}")
        ]))


@channel.use(ListenerSchema(listening_events=[BotGroupPermissionChangeEvent]))
async def get_BotJoinGroup(app: GraiaMiraiApplication, permissionchange: BotGroupPermissionChangeEvent):
    '''
    群内权限变动
    '''
    for qq in yaml_data['Basic']['Permission']['Admin']:
        await app.sendFriendMessage(qq, MessageChain.create([
            Plain("收到权限变动事件"),
            Plain(f"\n群号：{permissionchange.group.id}"),
            Plain(f"\n群名：{permissionchange.group.name}"),
            Plain(f"\n权限变更为：{permissionchange.current}")
        ]))


@channel.use(ListenerSchema(listening_events=[BotMuteEvent]))
async def get_BotJoinGroup(app: GraiaMiraiApplication, group: Group, mute: BotMuteEvent):
    '''
    被禁言
    '''
    for qq in yaml_data['Basic']['Permission']['Admin']:
        await app.sendFriendMessage(qq, MessageChain.create([
            Plain("收到禁言事件，已退出该群"),
            Plain(f"\n群号：{group.id}"),
            Plain(f"\n群名：{group.name}"),
            Plain(f"\n操作者：{mute.operator.name} | {mute.operator.id}")
        ]))
        await app.quit(group)


@channel.use(ListenerSchema(listening_events=[FriendMessage]))
async def friendTrans(app: GraiaMiraiApplication, friend: Friend, message: MessageChain):
    '''
    收到私信
    '''
    say = message.asDisplay()
    await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
        Plain(f"收到私信消息"),
        Plain(f"\n来源：{friend.id} | {friend.nickname}"),
        Plain(f"\n消息内容：{say}")
    ]))


@channel.use(ListenerSchema(listening_events=[MemberCardChangeEvent]))
async def main(app: GraiaMiraiApplication, events: MemberCardChangeEvent):
    '''
    群名片被修改
    '''
    if events.member.id == yaml_data['Basic']['MAH']['BotQQ']:
        if events.current != yaml_data['Basic']['BotName']:
            await app.sendFriendMessage(2948531755, MessageChain.create([
                Plain(f"检测到 {yaml_data['Basic']['BotName']} 群名片变动"),
                Plain(f"\n群号：{str(events.member.group.id)}"),
                Plain(f"\n群名：{events.member.group.name}"),
                Plain(f"\n被修改为：{events.current}"),
                Plain(f"\n以为你修改回：{yaml_data['Basic']['BotName']}")
            ]))
            await app.modifyMemberInfo(member=yaml_data['Basic']['MAH']['BotQQ'],
                                       info=MemberInfo(
                                           name=yaml_data['Basic']['BotName']),
                                       group=events.member.group.id)
            await app.sendGroupMessage(events.member.group.id,
                                       MessageChain.create([Plain(f"请不要修改我的群名片")]))
            await asyncio.sleep(2)


@channel.use(ListenerSchema(listening_events=[MemberJoinEvent]))
async def getMemberJoinEvent(app: GraiaMiraiApplication, events: MemberJoinEvent):
    a = 1
    if a == 2:
        msg = [
            Image_NetworkAddress(f"http://q1.qlogo.cn/g?b=qq&nk={str(events.member.id)}&s=4"),
            Plain(f"\n欢迎 {events.member.name} 加入本群\n")
        ]
        if group_data[events.member.group.id]["WelcomeMSG"]["Enabled"]:
            welcomeMsg = group_data[events.member.group.id]["WelcomeMSG"]['Message']
            msg.append(Plain(f"\n{welcomeMsg}"))
        await app.sendGroupMessage(events.member.group, MessageChain.create(msg))
