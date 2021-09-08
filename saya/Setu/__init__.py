from graia.saya import Saya, Channel
from graia.application.group import Group
from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.application.event.messages import GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.elements.internal import Image_UnsafeBytes

from util.limit import manual_limit
from util.RestControl import rest_control
from util.UserBlock import black_list_block
from config import yaml_data, group_data, sendmsg

from .setu import create_setu

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            headless_decorators=[rest_control(), black_list_block()]))
async def main(app: GraiaMiraiApplication, group: Group, message: MessageChain):

    saying = message.asDisplay().split(" ", 1)
    if saying[0] in ['色图', '涩图', '瑟图', 'setu']:

        manual_limit(group.id, "setu", 3)

        if yaml_data['Saya']['Setu']['Disabled']:
            return await sendmsg(app=app, group=group)
        elif 'Setu' in group_data[group.id]['DisabledFunc']:
            return await sendmsg(app=app, group=group)

        await app.sendGroupMessage(group, MessageChain.create([Image_UnsafeBytes(await create_setu())]))
