import json
import random

from pathlib import Path
from graia.saya import Channel
from graia.ariadne.model import Group, Member
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Plain, Source
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import FullMatch, Twilight

from util.text2image import create_image
from util.sendMessage import safeSendGroupMessage
from util.control import Function, Interval, Permission, Rest

channel = Channel.current()

Designs = json.loads(
    Path(__file__).parent.joinpath("DesignsDICT.json").read_text("UTF-8")
)["Designs"]


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("查看人设")])],
        decorators=[
            Function.require("CharacterDesignGenerator"),
            Permission.require(),
            Rest.rest_control(),
            Interval.require(),
        ],
    )
)
async def rand_designs(group: Group, member: Member, source: Source):
    msg = "你的人设：\n"
    for type in get_rand(member.id, group.id):
        msg += f"{type[0]}：{type[1]}\n"

    image = await create_image(msg)
    await safeSendGroupMessage(
        group, MessageChain.create([Image(data_bytes=image)]), quote=source.id
    )


def get_rand(qid: int, gid: int):
    i = 1
    s = 1
    designs_list = []
    for _i in Designs:
        for _ in Designs[_i]:
            s += 1

    for type in Designs:
        random.seed(qid + gid + i + s)
        designs_list.append([type, random.choice(Designs[type])])
        i += 1
    return designs_list


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("重载人设")])],
        decorators=[Permission.require(Permission.MASTER)],
    )
)
async def reoald_designs(group: Group):
    global Designs
    Designs = json.loads(
        Path(__file__).parent.joinpath("DesignsDICT.json").read_text("UTF-8")
    )["Designs"]
    await safeSendGroupMessage(group, MessageChain.create([Plain("重载完成")]))
