import random

from graia.saya import Channel
from graia.ariadne.model import Group
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.element import At, Face, Image, Plain

from config import yaml_data
from util.sendMessage import safeSendGroupMessage
from util.control import Function, Permission, Rest
from util.TextModeration import text_moderation_async

channel = Channel.current()


repdict = {}


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        decorators=[
            Function.require("Repeater"),
            Rest.rest_control(False),
            Permission.require(),
        ],
    )
)
async def repeater(group: Group, message: MessageChain):
    global repdict
    saying = message.asDisplay()
    ifpic = not message.has(Image)
    ifface = not message.has(Face)
    ifat = not message.has(At)
    if ifpic & ifface & ifat:
        if group.id not in repdict:
            repdict[group.id] = {"msg": saying, "times": 1, "last": ""}
        elif saying == repdict[group.id]["msg"]:
            repdict[group.id]["times"] = repdict[group.id]["times"] + 1
            if (
                repdict[group.id]["times"]
                == yaml_data["Saya"]["Repeater"]["RepeatTimes"]
                and saying != repdict[group.id]["last"]
            ):
                res = await text_moderation_async(saying)
                if res["status"]:
                    await safeSendGroupMessage(
                        group, MessageChain.create([Plain(saying)])
                    )
                    repdict[group.id] = {"msg": saying, "times": 1, "last": saying}
        else:
            repdict[group.id]["msg"] = saying
            repdict[group.id]["times"] = 1


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        decorators=[
            Function.require("Repeater"),
            Rest.rest_control(False),
            Permission.require(),
        ],
    )
)
async def repeateron(group: Group, message: MessageChain):

    if yaml_data["Saya"]["Repeater"]["Random"]["Disabled"]:
        return

    saying = message.asDisplay()
    randint = random.randint(1, yaml_data["Saya"]["Repeater"]["Random"]["Probability"])
    if randint == yaml_data["Saya"]["Repeater"]["Random"]["Probability"]:
        ifpic = not message.has(Image)
        ifface = not message.has(Face)
        ifat = not message.has(At)
        if ifpic & ifface & ifat:
            repdict[group.id] = {"msg": saying, "times": 1, "last": saying}
            res = await text_moderation_async(saying)
            if res["status"]:
                await safeSendGroupMessage(group, MessageChain.create([Plain(saying)]))
