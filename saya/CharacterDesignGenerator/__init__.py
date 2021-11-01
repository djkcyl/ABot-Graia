import json
import random

from pathlib import Path
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group, Member
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.literature import Literature
from graia.ariadne.message.element import Image, Plain, Source
from graia.saya.builtins.broadcast.schema import ListenerSchema

from config import yaml_data, group_data
from util.text2image import create_image
from util.limit import member_limit_check
from util.RestControl import rest_control
from util.UserBlock import group_black_list_block

saya = Saya.current()
channel = Channel.current()

Designs = json.loads(Path(__file__).parent.joinpath("DesignsDICT.json").read_text("UTF-8"))['Designs']


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Literature("查看人设")],
                            headless_decorators=[member_limit_check(15), rest_control(), group_black_list_block()]))
async def rand_designs(app: Ariadne, group: Group, member: Member, source: Source):

    if yaml_data['Saya']['CharacterDesignGenerator']['Disabled']:
        return
    elif 'CharacterDesignGenerator' in group_data[group.id]['DisabledFunc']:
        return

    msg = "你的人设：\n"
    for type in get_rand(member.id, group.id):
        msg += f"{type[0]}：{type[1]}\n"

    image = await create_image(msg)
    await app.sendGroupMessage(group, MessageChain.create([
        Image(data_bytes=image)
    ]), quote=source.id)


def get_rand(qid: int, gid: int):
    i = 1
    s = 1
    designs_list = []
    for _i in Designs:
        for _ in Designs[_i]:
            s += 1

    for type in Designs:
        random.seed(qid + gid + i + s)
        designs_list.append([
            type,
            random.choice(Designs[type])
        ])
        i += 1
    return designs_list


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Literature("/reload", "人设")],
                            headless_decorators=[member_limit_check(15), rest_control(), group_black_list_block()]))
async def reoald_designs(app: Ariadne, group: Group, member: Member):
    global Designs
    if member.id == yaml_data['Basic']['Permission']['Master']:
        Designs = json.loads(Path(__file__).parent.joinpath("DesignsDICT.json").read_text("UTF-8"))['Designs']
        await app.sendGroupMessage(group, MessageChain.create([Plain("重载完成")]))
