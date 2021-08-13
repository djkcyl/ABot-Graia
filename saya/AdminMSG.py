
from graia.saya import Saya, Channel
from graia.application.friend import Friend
from graia.application.group import MemberInfo
from graia.application.group import Group, Member
from graia.application import GraiaMiraiApplication
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.parser.literature import Literature
from graia.application.event.messages import GroupMessage, FriendMessage
from graia.application.message.elements.internal import MessageChain, Plain, Source, Quote, At

from config import yaml_data
from datebase.db import add_gold, all_sign_num, give_all_gold

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("1", allow_quote=True, skip_one_at_in_quote=True)]))
async def get_botQueue(app: GraiaMiraiApplication, member: Member, message: MessageChain, source: Source):
    if member.id in yaml_data['Basic']['Permission']['Admin']:
        if message.has(Quote):
            messageid = message.get(Quote)[0].origin.get(Source)[0].id
            try:
                await app.revokeMessage(messageid)
                await app.revokeMessage(source)
            except:
                pass


@channel.use(ListenerSchema(listening_events=[FriendMessage], inline_dispatchers=[Literature("全员充值")]))
async def main(app: GraiaMiraiApplication, friend: Friend, message: MessageChain):
    if friend.id == yaml_data['Basic']['Permission']['Master']:
        saying = message.asDisplay().split()
        await give_all_gold(int(saying[1]))
        await app.sendFriendMessage(friend, MessageChain.create([
            Plain(f"已向所有人充值 {saying[1]} 个游戏币")
        ]))


@channel.use(ListenerSchema(listening_events=[FriendMessage], inline_dispatchers=[Literature("充值")]))
async def main(app: GraiaMiraiApplication, friend: Friend, message: MessageChain):
    if friend.id == yaml_data['Basic']['Permission']['Master']:
        saying = message.asDisplay().split()
        await add_gold(saying[1], int(saying[2]))
        await app.sendFriendMessage(friend, MessageChain.create([
            Plain(f"已向 {saying[1]} 充值 {saying[2]} 个游戏币")
        ]))
