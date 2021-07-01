import random
import asyncio

from time import strftime, gmtime
from graia.application import group
from pydantic.types import confloat
from graia.saya import Saya, Channel
from graia.application.event.mirai import *
from graia.scheduler.timers import crontabify
from graia.application.event.messages import *
from graia.application.group import MemberInfo
from graia.broadcast.interrupt.waiter import Waiter
from graia.application import GraiaMiraiApplication
from graia.broadcast.interrupt import InterruptControl
from graia.scheduler.saya.schema import SchedulerSchema
from graia.application.message.elements.internal import *
from graia.application.interrupts import FriendMessageInterrupt
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.parser.literature import Literature

from config import Config, sendmsg


saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
inc = InterruptControl(bcc)


# baidu_Token_api = f'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={configs["API Key"]}&client_secret={configs["Secret Key"]}'
# r = requests.get(baidu_Token_api)
# _Token = json.loads(r.text)['access_token']
# print(_Token)


# @channel.use(ListenerSchema(listening_events=[GroupMessage]))
# async def message_review(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
#     global _Token
#     if group.id == 790380594:
#         message_id = message.getFirst(Source).id

#         # 判断是否包含图片
#         # if message.has(Image):
#         #     message_image = message.get(Image)

#         if message.has(Plain):
#             print("检测到文本")
#             message_text = message.asDisplay().replace(
#                 "[图片]", "").replace("[表情]", "").replace("\n", "").strip("")
#             censor = text_censor(message_text, _Token)
#             if censor["conclusionType"] != 1:
#                 await app.sendGroupMessage(group.id, MessageChain.create([Plain(censor["data"][0]["msg"])]))
#                 await app.revokeMessage(message_id)
#                 await app.mute(group, member.id, 5)
#                 # await app.unmute(group, member.id)

#         message_plain = message.asMerged()

#         # print(message.asDisplay())
#         # print(message.get(Image))
#         print(message_text)
#         # await app.sendGroupMessage(group.id, MessageChain.create([Plain("爬")]), quote=message_id)
#         # await app.revokeMessage(message_id)
#         # await app.mute(group, member.id, 2592000)
#         # await app.unmute(group, member.id)
#         # print(message_id)


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def atrep(app: GraiaMiraiApplication, group: Group, message: MessageChain, member: Member, source: Source):
    ifat = message.has(At)
    if ifat:
        ifa = message.get(At)[0].target == Config.Basic.MAH.BotQQ
        ifas = message.asDisplay().strip() == f"@{str(Config.Basic.MAH.BotQQ)}"
        if ifas:
            if ifa:
                if member.id == Config.Basic.Permission.Master:
                    await app.sendGroupMessage(group,
                                               MessageChain.create([
                                                   Plain(f"爹！")
                                               ]),
                                               quote=source.id)
                else:
                    await app.sendGroupMessage(group, MessageChain.create([
                        Plain(
                            f"我是{Config.Basic.Permission.MasterName}的机器人{Config.Basic.BotName}，如果有需要可以联系主人QQ”{str(Config.Basic.Permission.Master)}master“，添加{Config.Basic.BotName}好友后可以被拉到其他群（她会自动同意的），{Config.Basic.BotName}被群禁言后会自动退出该群。")
                    ]))


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("/mute")]))
async def message_revoke(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    if member.id in Config.Basic.Permission.Admin:
        mute_list = message.asDisplay().split()
        print(mute_list)
        qq = message.get(At)[0].target
        time = int(mute_list[2])
        await app.mute(group, qq, time)
    else:
        await app.sendGroupMessage(group, MessageChain.create([Plain("爬")]))


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("/unmute")]))
async def unmute(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    if member.id in Config.Basic.Permission.Admin:
        unmute_list = message.asDisplay().split()
        print(unmute_list)
        qq = message.get(At)[0].target
        await app.unmute(group, qq)
    else:
        await app.sendGroupMessage(group, MessageChain.create([Plain("爬")]))


@channel.use(ListenerSchema(listening_events=[FriendMessage], inline_dispatchers=[Literature("/unmute")]))
async def livegroup(app: GraiaMiraiApplication, friend: Friend, message: MessageChain):
    if friend.id in Config.Basic.Permission.Admin:
        say = message.asDisplay().split()
        groupid = say[1]
        try:
            await app.unmute(groupid, friend.id)
        except PermissionError:
            await app.sendFriendMessage(friend, MessageChain.create([Plain(f"权限不足，无法取消禁言")]))


if Config.Saya.MutePack.MaxTime * Config.Saya.MutePack.MaxMultiple * Config.Saya.MutePack.MaxSuperDoubleMultiple > 2592000:
    print("禁言套餐最大基础时长设定超过30天，请检查配置文件")
    exit()


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("我要禁言套餐")]))
async def random_mute(app: GraiaMiraiApplication, group: Group, member: Member):

    if Config.Saya.MutePack.Disabled:
        return await sendmsg(app=app, group=group)
    elif group.id in Config.Saya.MutePack.Blacklist:
        return await sendmsg(app=app, group=group)

    if member.id in Config.Basic.Permission.Admin:
        time = random.randint(60, 180)
    else:
        time = random.randint(60, Config.Saya.MutePack.MaxTime)
    multiple = random.randint(1, Config.Saya.MutePack.MaxMultiple)
    ftime = time * multiple
    srtftime = strftime("%H:%M:%S", gmtime(ftime))
    if random.randint(1, Config.Saya.MutePack.MaxJackpotProbability) == Config.Saya.MutePack.MaxJackpotProbability:
        try:
            await app.mute(group, member, 2592000)
            await app.sendGroupMessage(group, MessageChain.create([AtAll(), Plain(f"恭喜{member.name}中了头奖！获得30天禁言！")]))
            await app.sendFriendMessage(Config.Basic.Permission.Master, MessageChain.create(Plain(f"恭喜 {group.name} 群里的 {member.name} 中了禁言头奖")))
            quit()
        except PermissionError:
            await app.sendGroupMessage(group, MessageChain.create([Plain(f"权限不足，无法使用！\n使用该功能{Config.Basic.BotName}需要为管理")]))
    elif Config.Saya.MutePack.SuperDouble and random.randint(1, Config.Saya.MutePack.MaxSuperDoubleProbability) == Config.Saya.MutePack.MaxSuperDoubleProbability:
        try:
            ftime = ftime * Config.Saya.MutePack.MaxSuperDoubleMultiple
            srtftime = strftime("%d:%H:%M:%S", gmtime(ftime))
            await app.mute(group, member, ftime)
            await app.sendGroupMessage(group, MessageChain.create([Plain(f"恭喜你抽中了 {time} 秒禁言套餐！倍率为 {multiple}！\n超级加倍！\n最终时长为 {srtftime}")]))
        except PermissionError:
            await app.sendGroupMessage(group, MessageChain.create([Plain(f"权限不足，无法使用！\n使用该功能{Config.Basic.BotName}需要为管理员权限或更高")]))
    else:
        try:
            await app.mute(group, member, ftime)
            await app.sendGroupMessage(group, MessageChain.create([Plain(f"恭喜你抽中了 {time} 秒禁言套餐！倍率为 {multiple}\n最终时长为 {srtftime}")]))
        except PermissionError:
            await app.sendGroupMessage(group, MessageChain.create([Plain(f"权限不足，无法使用！\n使用该功能{Config.Basic.BotName}需要为管理员权限或更高")]))


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("/ping943")]))
async def ping943(app: GraiaMiraiApplication, group: Group, message: MessageChain):
    saylist = message.asDisplay().split()
    saylistnum = len(saylist)
    if saylistnum == 3:
        if saylist[1] == "t":
            i = 0
            atnum = []
            while i < int(saylist[2]):
                atnum.append(At(target=568248266))
                atnum.append(Plain(" "))
                i += 1
            print(atnum)
            await app.sendGroupMessage(group, MessageChain.create([Plain(f"正在ping {i} 次")]))
            await app.sendGroupMessage(group, MessageChain.create(atnum))
        else:
            await app.sendGroupMessage(group, MessageChain.create([Plain("使用方法：/ping943 [t *int]")]))
    elif saylistnum == 2:
        if saylist[1] == "t":
            await app.sendGroupMessage(group, MessageChain.create([Plain("请输入ping次数")]))
        else:
            await app.sendGroupMessage(group, MessageChain.create([Plain("使用方法：/ping943 [t *int]")]))
    elif saylist[0] == "/ping943":
        await app.sendGroupMessage(group, MessageChain.create([At(568248266)]))


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("/setnick")]))
async def unmute(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    if member.id in Config.Basic.Permission.Admin:
        saylist = message.asDisplay().split()
        qq = message.get(At)[0].target
        await app.modifyMemberInfo(qq, MemberInfo(name=(saylist[2])), group)
    else:
        await app.sendGroupMessage(group, MessageChain.create([Plain("爬")]))


# 草(
@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("草", allow_quote=True)]))
async def a_plant(app: GraiaMiraiApplication, group: Group):
    await app.sendGroupMessage(group, MessageChain.create([
        Plain(f"一种植物（")
    ]))


@channel.use(ListenerSchema(listening_events=[BotJoinGroupEvent]))
async def get_BotJoinGroup(app: GraiaMiraiApplication, joingroup: BotJoinGroupEvent):
    for qq in Config.Basic.Permission.Admin:
        await app.sendFriendMessage(qq, MessageChain.create([
            Plain("收到加入群聊事件"),
            Plain(f"\n群号：{joingroup.group.id}"),
            Plain(f"\n群名：{joingroup.group.name}")
        ]))


@channel.use(ListenerSchema(listening_events=[BotLeaveEventKick]))
async def get_BotJoinGroup(app: GraiaMiraiApplication, member: Member, kickgroup: BotLeaveEventKick):
    for qq in Config.Basic.Permission.Admin:
        await app.sendFriendMessage(qq, MessageChain.create([
            Plain("收到被踢出群聊事件"),
            Plain(f"\n群号：{kickgroup.group.id}"),
            Plain(f"\n群名：{kickgroup.group.name}"),
            Plain(f"\n操作人：{member.name} | {member.id}")
        ]))


@channel.use(ListenerSchema(listening_events=[BotGroupPermissionChangeEvent]))
async def get_BotJoinGroup(app: GraiaMiraiApplication, permissionchange: BotGroupPermissionChangeEvent):
    for qq in Config.Basic.Permission.Admin:
        await app.sendFriendMessage(qq, MessageChain.create([
            Plain("收到权限变动事件"),
            Plain(f"\n群号：{permissionchange.group.id}"),
            Plain(f"\n群名：{permissionchange.group.name}"),
            Plain(f"\n权限变更为：{permissionchange.current}")
        ]))


@channel.use(ListenerSchema(listening_events=[BotMuteEvent]))
async def get_BotJoinGroup(app: GraiaMiraiApplication, group: Group, mute: BotMuteEvent):
    for qq in Config.Basic.Permission.Admin:
        await app.sendFriendMessage(qq, MessageChain.create([
            Plain("收到禁言事件"),
            Plain(f"\n群号：{group.id}"),
            Plain(f"\n群名：{group.name}"),
            Plain(f"\n操作者：{mute.operator.name} | {mute.operator.id}")
        ]))


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("1", allow_quote=True, skip_one_at_in_quote=True)]))
async def get_botQueue(app: GraiaMiraiApplication, member: Member, message: MessageChain, source: Source):
    if member.id in Config.Basic.Permission.Admin:
        messageid = message.get(Quote)[0].origin.get(Source)[0].id
        try:
            await app.revokeMessage(messageid)
            await app.revokeMessage(source)
        except:
            pass


@channel.use(ListenerSchema(listening_events=[FriendMessage]))
async def friendTrans(app: GraiaMiraiApplication, friend: Friend, message: MessageChain):
    say = message.asDisplay()
    await app.sendFriendMessage(Config.Basic.Permission.Master, MessageChain.create([
        Plain(f"收到私信消息"),
        Plain(f"\n来源：{friend.id} | {friend.nickname}"),
        Plain(f"\n消息内容：{say}")
    ]))


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("/viveall")]))
async def viveall(app: GraiaMiraiApplication, member: Member, group: Group):
    if member.id == Config.Basic.Permission.Master:
        userlist = await app.memberList(group)
        usernum = len(userlist)
        await app.sendGroupMessage(group, MessageChain.create([Plain(f"当前群人数共有 {usernum} 人\n{Config.Basic.BotName}如为管理发送/kickall即可将全部管理权限以下群员踢出群聊")]))


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("/kickall")]))
async def kickall(app: GraiaMiraiApplication, member: Member, group: Group):
    if member.id == Config.Basic.Permission.Master:
        memberlist = await app.memberList()
        for member in memberlist:
            try:
                await app.kick(group, member)
            except PermissionError:
                break
            await asyncio.sleep(0.3)


# @channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("/bantime")]))
# async def kickall(app: GraiaMiraiApplication, group: Group):
#     n1 = '2021-06-16 18:00:19'
#     struct_time1, struct_time2 = time.time(), time.strptime(n1, '%Y-%m-%d %H:%M:%S')
#     struct_time2 = time.mktime(struct_time2)
#     diff_time = struct_time2 - struct_time1
#     struct_time = time.gmtime(diff_time)

#     await app.sendGroupMessage(group, MessageChain.create([
#         Plain('距离解封还有{2}日{3}小时{4}分钟{5}秒'.format(
#             struct_time.tm_year-1970,
#             struct_time.tm_mon-1,
#             struct_time.tm_mday-1,
#             struct_time.tm_hour,
#             struct_time.tm_min,
#             struct_time.tm_sec
#         ))]))


# @channel.use(ListenerSchema(listening_events=[BotInvitedJoinGroupRequestEvent]))
# async def accept(app: GraiaMiraiApplication, invite: BotInvitedJoinGroupRequestEvent):
#     await app.sendFriendMessage(Config.Basic.Permission.Master, MessageChain.create([
#         Plain(f"收到邀请入群事件"),
#         Plain(f"\n邀请者：{invite.supplicant} | {invite.nickname}"),
#         Plain(f"\n群号：{invite.groupId}"),
#         Plain(f"\n群名：{invite.groupName}")
#     ]))
#     await invite.accept()


# @channel.use(SchedulerSchema(crontabify("* * * * * *")))
# async def something_scheduled(app: GraiaMiraiApplication):
#     await app.sendFriendMessage(Config.Basic.Permission.Master, MessageChain.create([Plain("消息发送测试")]))


# @channel.use(ListenerSchema(listening_events=[FriendMessage], inline_dispatchers=[Literature("/grouplist")]))
# async def main(app: GraiaMiraiApplication, friend: Friend):
#     if friend.id == Config.Basic.Permission.Master:
#         grouplist = await app.groupList()
#         grouplist = list(set(grouplist))
#         # grouplist = grouplist.sort()
#         print(grouplist)


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("色图")]))
async def main(app: GraiaMiraiApplication, group: Group):
    await app.sendGroupMessage(group, MessageChain.create([Image_LocalFile("./saya/Message/setu_qr.png")]))


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("流汗黄豆.jpg")]))
async def main(app: GraiaMiraiApplication, group: Group, member: Member):
    if member.id == Config.Basic.Permission.Master:
        await app.sendGroupMessage(group, MessageChain.create([Image_LocalFile("./saya/Message/huangdou.jpg")]))
    else:
        await app.sendGroupMessage(group, MessageChain.create([At(member.id), Image_LocalFile("./saya/Message/huangdou.jpg")]))


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("好耶")]))
async def main(app: GraiaMiraiApplication, group: Group):
    await app.sendGroupMessage(group, MessageChain.create([Image_LocalFile("./saya/Message/haoye.png")]))


@channel.use(ListenerSchema(listening_events=[MemberCardChangeEvent]))
async def main(app: GraiaMiraiApplication, events: MemberCardChangeEvent):
    if events.member.id == Config.Basic.MAH.BotQQ:
        if events.current != Config.Basic.BotName:
            await app.sendFriendMessage(2948531755, MessageChain.create([
                Plain(f"检测到 {Config.Basic.BotName} 群名片变动"),
                Plain(f"\n群号：{str(events.member.group.id)}"),
                Plain(f"\n群名：{events.member.group.name}"),
                Plain(f"\n被修改为：{events.current}"),
                Plain(f"\n以为你修改回：{Config.Basic.BotName}")
            ]))
            await app.modifyMemberInfo(member=Config.Basic.MAH.BotQQ,
                                    info=MemberInfo(name=Config.Basic.BotName),
                                    group=events.member.group.id)
            await app.sendGroupMessage(events.member.group.id,
                                    MessageChain.create([Plain(f"请不要修改我的群名片")]))
            await asyncio.sleep(2)