import httpx

from graia.saya import Saya, Channel
from graia.application.group import Group, Member
from graia.application import GraiaMiraiApplication
from graia.application.event.messages import GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.elements.internal import MessageChain, Source, Plain, Image_NetworkAddress, At

from util.limit import manual_limit
from config import sendmsg, yaml_data
from util.UserBlock import group_black_list_block

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            headless_decorators=[group_black_list_block()]))
async def trashCard(app: GraiaMiraiApplication, group: Group, member: Member, message: MessageChain, source: Source):
    saying = message.asDisplay()
    key = ["废物证申请", "我是废物"]
    if saying in key:
        manual_limit(group.id, "TrashCard", 5)
        if yaml_data['Saya']['TrashCard']['Disabled']:
            return await sendmsg(app=app, group=group)

        url = 'http://a60.one:11451/getCard'
        data = {
            "qqid": member.id,
            "groupname": group.name
        }

        async with httpx.AsyncClient() as client:
            r = await client.post(url, json=data)
        card = r.json()
        app.logger.info(card)

        if "code" in card:
            await app.sendGroupMessage(group, MessageChain.create([
                At(member.id),
                Plain(" "),
                Plain(card['msg']),
                Plain(card['id'])
            ]), quote=source.id)
            await app.sendGroupMessage(group, MessageChain.create([Image_NetworkAddress(card['pic'])]))
