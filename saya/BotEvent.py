import asyncio

from typing import Optional
from graia.saya import Saya, Channel
from graia.application.group import Group
from graia.application.friend import Friend
from graia.application.group import MemberInfo
from graia.application import GraiaMiraiApplication
from graia.broadcast.interrupt.waiter import Waiter
from graia.broadcast.interrupt import InterruptControl
from graia.application.event.messages import FriendMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.event.lifecycle import ApplicationLaunched, ApplicationShutdowned
from graia.application.message.elements.internal import MessageChain, Plain, Image_NetworkAddress
from graia.application.event.mirai import NewFriendRequestEvent, BotInvitedJoinGroupRequestEvent, BotJoinGroupEvent, BotLeaveEventKick, BotGroupPermissionChangeEvent, BotMuteEvent, MemberCardChangeEvent, MemberJoinEvent

from config import save_config, yaml_data, group_data, group_list
from .AdminConfig import groupInitData

saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
inc = InterruptControl(bcc)


@channel.use(ListenerSchema(listening_events=[ApplicationLaunched]))
async def groupDataInit(app: GraiaMiraiApplication):
    '''
    Graia 成功启动
    '''
    groupList = await app.groupList()
    groupNum = len(groupList)
    await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
        Plain(f"ABot-Graia成功启动，正在初始化，请稍后。"),
        Plain(f"\n当前 {yaml_data['Basic']['BotName']} 共加入了 {groupNum} 个群")
    ]))
    i = 0
    for group in groupList:
        if group.id not in group_data:
            group_data[group.id] = groupInitData
            print(group_data[group.id])
            print(f"已为 {group.id} 进行初始化配置")
            i += 1
    save_config()
    msg = [Plain(f"初始化结束")]
    if i > 0:
        msg.append(Plain(f"\n以为 {str(1)} 个群进行了初始化配置"))
    await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create(msg))


@channel.use(ListenerSchema(listening_events=[ApplicationShutdowned]))
async def groupDataInit(app: GraiaMiraiApplication):
    await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
        Plain(f"正在关闭")
    ]))


@channel.use(ListenerSchema(listening_events=[NewFriendRequestEvent]))
async def get_BotJoinGroup(app: GraiaMiraiApplication, events: NewFriendRequestEvent):
    '''
    收到好友申请
    '''
    sourceGroup: Optional[int] = events.sourceGroup
    for qq in yaml_data['Basic']['Permission']['Admin']:
        await app.sendFriendMessage(qq, MessageChain.create([
            Plain("收到添加好友事件"),
            Plain(f"\nQQ：{events.supplicant}"),
            Plain(f"\n昵称：{events.nickname}"),
            Plain(f"\n来自群：{sourceGroup}"),
            Plain(f"\n状态：已通过申请\n\n{events.message.upper()}")
        ]))
    await events.accept()


@channel.use(ListenerSchema(listening_events=[BotInvitedJoinGroupRequestEvent]))
async def accept(app: GraiaMiraiApplication, invite: BotInvitedJoinGroupRequestEvent):
    '''
    被邀请入群
    '''
    if invite.groupId in group_list['white']:
        await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
            Plain("收到邀请入群事件"),
            Plain(f"\n邀请者：{invite.supplicant} | {invite.nickname}"),
            Plain(f"\n群号：{invite.groupId}"),
            Plain(f"\n群名：{invite.groupName}"),
            Plain("\n该群为白名单群，已同意加入")
        ]))
        await invite.accept("")
    else:
        await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
            Plain(f"收到邀请入群事件"),
            Plain(f"\n邀请者：{invite.supplicant} | {invite.nickname}"),
            Plain(f"\n群号：{invite.groupId}"),
            Plain(f"\n群名：{invite.groupName}"),
            Plain(f"\n\n请发送“同意”或“拒绝”")
        ]))

        @Waiter.create_using_function([FriendMessage])
        async def waiter(waiter_friend: Friend, waiter_message: MessageChain):
            if waiter_friend.id == yaml_data['Basic']['Permission']['Master']:
                saying = waiter_message.asDisplay()
                if saying == "同意":
                    return True
                elif saying == "拒绝":
                    return False
                else:
                    await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
                        Plain("请发送同意或拒绝")
                    ]))
        try:
            if await asyncio.wait_for(inc.wait(waiter), timeout=300):
                await invite.accept()
                await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
                    Plain("已同意申请")
                ]))
            else:
                await invite.reject("主人拒绝加入该群")
                await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
                    Plain("已拒绝申请")
                ]))

        except asyncio.TimeoutError:
            await invite.reject("由于主人长时间未审核，已自动拒绝")
            await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
                Plain("申请超时已自动拒绝")
            ]))


@channel.use(ListenerSchema(listening_events=[BotJoinGroupEvent]))
async def get_BotJoinGroup(app: GraiaMiraiApplication, joingroup: BotJoinGroupEvent):
    '''
    收到入群事件
    '''
    if joingroup.group.id not in group_list['white']:
        return await app.quit(joingroup.group.id)

    if joingroup.group.id not in group_data:
        group_data[joingroup.group.id] = groupInitData
        print("已为该群初始化配置文件")
        save_config()
        await app.sendGroupMessage(joingroup.group.id, MessageChain.create([
            Plain(f"我是{yaml_data['Basic']['Permission']['MasterName']}"),
            Plain(f"的机器人{yaml_data['Basic']['BotName']}，"),
            Plain(f"如果有需要可以联系主人QQ”{str(yaml_data['Basic']['Permission']['Master'])}“，"),
            Plain(f"添加{yaml_data['Basic']['BotName']}好友后请私聊说明用途后即可拉进其他群，主人看到后会选择是否同意入群"),
            Plain(f"\n{yaml_data['Basic']['BotName']}被群禁言后会自动退出该群。"),
            Plain(f"\n发送 <菜单> 可以查看功能列表"),
            Plain(f"\n拥有管理员以上权限可以使用 <管理员功能菜单> 来开关功能"),
            Plain(f"\n\n@不会触发任何功能"),
            Plain(f"\n@不会触发任何功能"),
            Plain(f"\n@不会触发任何功能")
        ]))

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
    groupBlackList = group_list['white']
    try:
        groupBlackList.remove(kickgroup.group.id)
    except:
        pass
    group_list['white'] = groupBlackList
    save_config()

    for qq in yaml_data['Basic']['Permission']['Admin']:
        await app.sendFriendMessage(qq, MessageChain.create([
            Plain("收到被踢出群聊事件"),
            Plain(f"\n群号：{kickgroup.group.id}"),
            Plain(f"\n群名：{kickgroup.group.name}"),
            Plain(f"\n已添加至黑名单")
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
    groupBlackList = group_list['white']
    try:
        groupBlackList.remove(group.id)
    except:
        pass
    group_list['white'] = groupBlackList
    save_config()

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
    if not friend.id == yaml_data['Basic']['Permission']['Master']:
        await app.sendFriendMessage(friend, MessageChain.create([Plain("私信不会触发任何功能，触发功能请前往群聊触发")]))
        say = MessageChain.join(MessageChain.create([
            Plain(f"收到私信消息"),
            Plain(f"\n来源：{friend.id} | {friend.nickname}"),
            Plain(f"\n消息内容：\n\n")
        ]), message)
        await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], say.asSendable())


@channel.use(ListenerSchema(listening_events=[MemberCardChangeEvent]))
async def main(app: GraiaMiraiApplication, events: MemberCardChangeEvent):
    '''
    群名片被修改
    '''
    if events.member.id == yaml_data['Basic']['MAH']['BotQQ']:
        if events.current != yaml_data['Basic']['BotName']:
            await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
                Plain(f"检测到 {yaml_data['Basic']['BotName']} 群名片变动"),
                Plain(f"\n群号：{str(events.member.group.id)}"),
                Plain(f"\n群名：{events.member.group.name}"),
                Plain(f"\n被修改为：{events.current}"),
                Plain(f"\n已为你修改回：{yaml_data['Basic']['BotName']}")
            ]))
            await app.modifyMemberInfo(member=yaml_data['Basic']['MAH']['BotQQ'],
                                       info=MemberInfo(name=yaml_data['Basic']['BotName']),
                                       group=events.member.group.id)
            await app.sendGroupMessage(events.member.group.id,
                                       MessageChain.create([Plain(f"请不要修改我的群名片")]))
            await asyncio.sleep(2)


# 群内事件
@channel.use(ListenerSchema(listening_events=[MemberJoinEvent]))
async def getMemberJoinEvent(app: GraiaMiraiApplication, events: MemberJoinEvent):
    '''
    有人加入群聊
    '''
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
