from graia.saya import Saya, Channel
from graia.application.group import Group
from graia.application import GraiaMiraiApplication
from graia.broadcast.interrupt import InterruptControl
from graia.application.event.messages import GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.parser.literature import Literature
from graia.application.message.elements.internal import MessageChain, Plain, At, Image_LocalFile

from config import yaml_data, group_data


saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
inc = InterruptControl(bcc)


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def a_plant(app: GraiaMiraiApplication, group: Group, message: MessageChain):
    
    if yaml_data['Saya']['Message']['Disabled']:
        return
    elif 'Message' in group_data[group.id]['DisabledFunc']:
        return
    
    saying = message.asDisplay()
    if saying == "草":
        await app.sendGroupMessage(group, MessageChain.create([
            Plain(f"一种植物（")
        ]))
    if saying == "好耶":
        await app.sendGroupMessage(group, MessageChain.create([
            Image_LocalFile("./saya/Message/haoye.png")
        ]))
    if saying == "流汗黄豆.jpg":
        await app.sendGroupMessage(group, MessageChain.create([
            Image_LocalFile("./saya/Message/huangdou.jpg")
        ]))
