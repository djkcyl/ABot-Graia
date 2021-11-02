from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group
from graia.ariadne.message.element import Image
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.parser.literature import Literature
from graia.saya.builtins.broadcast.schema import ListenerSchema

from util.limit import group_limit_check
from config import yaml_data, group_data
from util.RestControl import rest_control
from util.UserBlock import group_black_list_block

from .setu import create_setu

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Literature("色图")],
                            decorators=[group_limit_check(5), rest_control(), group_black_list_block()]))
async def main(app: Ariadne, group: Group):

    if yaml_data['Saya']['Setu']['Disabled']:
        return
    elif 'Setu' in group_data[str(group.id)]['DisabledFunc']:
        return

    await app.sendGroupMessage(group, MessageChain.create([
        Image(data_bytes=await create_setu())
    ]))
