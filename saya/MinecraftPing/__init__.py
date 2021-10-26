from graia.saya import Saya, Channel
from graia.application.group import Group
from graia.application import GraiaMiraiApplication
from graia.application.event.messages import GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.parser.literature import Literature
from graia.application.message.elements.internal import MessageChain, Plain

from util.limit import group_limit_check
from config import yaml_data, group_data
from util.UserBlock import group_black_list_block

from .mcping import mcping

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Literature("/mcping")],
                            headless_decorators=[group_limit_check(15), group_black_list_block()]))
async def minecraft_ping(app: GraiaMiraiApplication, group: Group, message: MessageChain):

    if yaml_data['Saya']['MinecraftPing']['Disabled']:
        return
    elif 'MinecraftPing' in group_data[group.id]['DisabledFunc']:
        return

    saying = message.asDisplay().split()
    if len(saying) == 2:
        # try:
            send_msg = await mcping(saying[1])
            # print(send_msg)
            await app.sendGroupMessage(str(group.id), MessageChain.create(send_msg))
        # except:
        #     await app.sendGroupMessage(str(group.id), MessageChain.create([Plain("用法：/mcping 服务器地址")]))
    else:
        await app.sendGroupMessage(str(group.id), MessageChain.create([Plain("用法：/mcping 服务器地址")]))
