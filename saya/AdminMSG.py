from graia.application import GraiaMiraiApplication
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.event.messages import *
from graia.application.event.mirai import *
from graia.application.group import MemberInfo
from graia.application.message.elements.internal import *
from graia.application.message.parser.literature import Literature

from config import yaml_data

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("1", allow_quote=True, skip_one_at_in_quote=True)]))
async def get_botQueue(app: GraiaMiraiApplication, member: Member, message: MessageChain, source: Source):
    if member.id in yaml_data['Basic']['Permission']['Admin']:
        messageid = message.get(Quote)[0].origin.get(Source)[0].id
        try:
            await app.revokeMessage(messageid)
            await app.revokeMessage(source)
        except:
            pass


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("/setnick")]))
async def unmute(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    if member.id in yaml_data['Basic']['Permission']['Admin']:
        saylist = message.asDisplay().split()
        qq = message.get(At)[0].target
        await app.modifyMemberInfo(qq, MemberInfo(name=(saylist[2])), group)


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("/mute")]))
async def message_revoke(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    if member.id in yaml_data['Basic']['Permission']['Admin']:
        mute_list = message.asDisplay().split()
        print(mute_list)
        qq = message.get(At)[0].target
        time = int(mute_list[2])
        await app.mute(group, qq, time)


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("/unmute")]))
async def unmute(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    if member.id in yaml_data['Basic']['Permission']['Admin']:
        unmute_list = message.asDisplay().split()
        print(unmute_list)
        qq = message.get(At)[0].target
        await app.unmute(group, qq)


@channel.use(ListenerSchema(listening_events=[FriendMessage], inline_dispatchers=[Literature("/unmute")]))
async def livegroup(app: GraiaMiraiApplication, friend: Friend, message: MessageChain):
    if friend.id in yaml_data['Basic']['Permission']['Admin']:
        say = message.asDisplay().split()
        groupid = say[1]
        try:
            await app.unmute(groupid, friend.id)
        except PermissionError:
            await app.sendFriendMessage(friend, MessageChain.create([Plain(f"权限不足，无法取消禁言")]))
