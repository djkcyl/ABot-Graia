import json
import requests

from graia.saya import Saya, Channel
from graia.application.group import Group, Member
from graia.application import GraiaMiraiApplication
from graia.application.event.messages import GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.parser.literature import Literature
from graia.application.message.elements.internal import MessageChain, Plain, At

from config import yaml_data, group_data, sendmsg
from util.limit import member_limit_check
from util.RestControl import rest_control

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Literature("emoji")],
                            headless_decorators=[rest_control(), member_limit_check(5)]))
async def fun_dict(app: GraiaMiraiApplication, group: Group, message: MessageChain, member: Member):

    if yaml_data['Saya']['ChickEmoji']['Disabled']:
        return await sendmsg(app=app, group=group)
    elif 'ChickEmoji' in group_data[group.id]['DisabledFunc']:
        return await sendmsg(app=app, group=group)

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
    emoji = json.loads(requests.post(api_url,
                                     json=api_data,
                                     headers=api_headers).text)
    # print(emoji)
    await app.sendGroupMessage(str(group.id), MessageChain.create([
        At(member.id),
        Plain("\n" + emoji["translation"])
    ]))
