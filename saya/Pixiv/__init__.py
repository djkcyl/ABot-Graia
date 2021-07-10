import json
import requests

from graia.application import GraiaMiraiApplication
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.event.messages import *
from graia.application.event.mirai import *
from graia.application.message.elements.internal import *

from config import yaml_data, sendmsg

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def main(app: GraiaMiraiApplication, group: Group, message: MessageChain):
    
    saying = message.asDisplay()
    if saying in ['色图', '涩图', 'setu']:
        if yaml_data['Saya']['Pixiv']['Disabled']:
            return await sendmsg(app=app, group=group)
        elif group.id in yaml_data['Saya']['Pixiv']['Blacklist']:
            return await sendmsg(app=app, group=group)
        picid = json.loads(requests.get('http://a60.one:404').text)['pic']
        await app.sendGroupMessage(group, MessageChain.create([Image_NetworkAddress(f"http://pic.a60.one:88/{picid}.jpg")]))