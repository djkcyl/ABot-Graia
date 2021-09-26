from graia.saya import Saya, Channel
from graia.application.group import Group
from graia.application import GraiaMiraiApplication
from graia.application.message.chain import MessageChain
from graia.application.event.messages import GroupMessage
from graia.application.message.parser.kanata import Kanata
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.parser.signature import FullMatch
from graia.application.message.elements.internal import Image_UnsafeBytes

from util.limit import group_limit_check
from config import yaml_data, group_data
from util.RestControl import rest_control
from util.UserBlock import black_list_block

from .setu import create_setu

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Kanata([FullMatch("色图|涩图|瑟图|setu")])],
                            headless_decorators=[group_limit_check(5), rest_control(), black_list_block()]))
async def main(app: GraiaMiraiApplication, group: Group):

    if yaml_data['Saya']['Setu']['Disabled']:
        return
    elif 'Setu' in group_data[group.id]['DisabledFunc']:
        return

    await app.sendGroupMessage(group, MessageChain.create([
        Image_UnsafeBytes(await create_setu())
    ]))
