import httpx

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group, Member
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.literature import Literature
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.element import Source, Plain, Image, At

from config import yaml_data
from util.limit import member_limit_check
from util.UserBlock import group_black_list_block

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Literature("我是废物")],
                            headless_decorators=[member_limit_check(5), group_black_list_block()]))
async def trashCard(app: Ariadne, group: Group, member: Member, source: Source):
    if yaml_data['Saya']['TrashCard']['Disabled']:
        return

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
        await app.sendGroupMessage(group, MessageChain.create([Image(url=card['pic'])]))
