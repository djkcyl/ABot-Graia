import httpx

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group, Member
from graia.ariadne.message.element import Plain, At
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.literature import Literature

from config import yaml_data, group_data
from util.sendMessage import safeSendGroupMessage
from util.control import Permission, Interval, Rest

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Literature("emoji")],
                            decorators=[Rest.rest_control(), Permission.require(), Interval.require(30)]))
async def fun_dict(app: Ariadne, group: Group, message: MessageChain, member: Member):

    if yaml_data['Saya']['ChickEmoji']['Disabled']:
        return
    elif 'ChickEmoji' in group_data[str(group.id)]['DisabledFunc']:
        return

    saying = message.asDisplay().split()
    api_url = "https://api.jikipedia.com/go/translate_plaintext"
    api_data = {
        "content": saying[1]
    }
    api_headers = {
        "Client": "web",
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": "https://jikipedia.com"
    }
    async with httpx.AsyncClient as client:
        r = await client.post(api_url, json=api_data, headers=api_headers)
    emoji = r.json()
    await safeSendGroupMessage(str(group.id), MessageChain.create([
        At(member.id),
        Plain("\n" + emoji["translation"])
    ]))
