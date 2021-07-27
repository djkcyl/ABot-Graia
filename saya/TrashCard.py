import requests

from graia.application import GraiaMiraiApplication
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.event.messages import *
from graia.application.event.mirai import *
from graia.application.message.elements.internal import *


from config import sendmsg, yaml_data

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def trashCard(app: GraiaMiraiApplication, group: Group, member: Member, message: MessageChain, source: Source):
    saying = message.asDisplay()
    key = ["废物证申请", "我是废物"]
    if saying in key:

        if yaml_data['Saya']['TrashCard']['Disabled']:
            return await sendmsg(app=app, group=group)

        url = 'http://a60.one:11451/getCard'
        data = {
            "qqid": member.id,
            "groupname": group.name
        }

        card = requests.post(url, json=data).json()
        print(card)

        if "code" in card:
            await app.sendGroupMessage(group, MessageChain.create([
                At(member.id),
                Plain(" "),
                Plain(card['msg']),
                Plain(card['id'])
            ]), quote=source.id)
            await app.sendGroupMessage(group, MessageChain.create([Image_NetworkAddress(card['pic'])]))