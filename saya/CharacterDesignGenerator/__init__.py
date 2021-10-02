import json
import random

from pathlib import Path
from graia.saya import Saya, Channel
from graia.application.group import Group, Member
from graia.application import GraiaMiraiApplication
from graia.application.event.messages import GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.parser.literature import Literature
from graia.application.message.elements.internal import Image_UnsafeBytes, MessageChain, Source

from util.text2image import create_image
from util.limit import member_limit_check
from util.RestControl import rest_control
from util.UserBlock import group_black_list_block
from config import yaml_data, sendmsg, group_data

saya = Saya.current()
channel = Channel.current()

DesignsDICT = json.loads(Path(__file__).parent.joinpath("DesignsDICT.json").read_text("UTF-8"))
Designs = DesignsDICT['Designs']


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Literature("查看人设")],
                            headless_decorators=[member_limit_check(15), rest_control(), group_black_list_block()]))
async def rand_designs(app: GraiaMiraiApplication, group: Group, member: Member, source: Source):

    if yaml_data['Saya']['CharacterDesignGenerator']['Disabled']:
        return await sendmsg(app=app, group=group)
    elif 'CharacterDesignGenerator' in group_data[group.id]['DisabledFunc']:
        return await sendmsg(app=app, group=group)

    msg = "你的人设：\n"
    for type in get_rand(member.id, group.id):
        msg += f"{type[0]}：{type[1]}\n"

    image = await create_image(msg)
    await app.sendGroupMessage(group, MessageChain.create([
        Image_UnsafeBytes(image.getvalue())
    ]), quote=source)


def get_rand(qid: int, gid: int):
    i = 1
    designs_list = []
    for type in Designs:
        random.seed((qid + gid + i))
        designs_list.append([
            type,
            random.choice(Designs[type])
        ])
        i += 1
    return designs_list
