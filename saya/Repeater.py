import random

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.element import Face, Image, Plain, At

from config import yaml_data, group_data
from util.RestControl import rest_control
from util.UserBlock import group_black_list_block
from util.TextModeration import text_moderation

saya = Saya.current()
channel = Channel.current()


repdict = {}


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            headless_decorators=[rest_control(), group_black_list_block()]))
async def repeater(app: Ariadne, group: Group, message: MessageChain):

    if yaml_data['Saya']['Repeater']['Disabled']:
        return
    elif 'Repeater' in group_data[group.id]['DisabledFunc']:
        return

    global repdict
    saying = message.asDisplay()
    ifpic = not message.has(Image)
    ifface = not message.has(Face)
    ifat = not message.has(At)
    if ifpic & ifface & ifat:
        if group.id not in repdict:
            repdict[group.id] = {'msg': saying, 'times': 1, 'last': ""}
        elif saying == repdict[group.id]['msg']:
            repdict[group.id]['times'] = repdict[group.id]['times'] + 1
            if repdict[group.id]['times'] == yaml_data['Saya']['Repeater']['RepeatTimes'] and saying != repdict[group.id]['last']:
                res = await text_moderation(saying)
                if res['Suggestion'] == "Pass":
                    await app.sendGroupMessage(group, MessageChain.create([Plain(saying)]))
                    repdict[group.id] = {'msg': saying, 'times': 1, 'last': saying}
        else:
            repdict[group.id]['msg'] = saying
            repdict[group.id]['times'] = 1


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            headless_decorators=[rest_control(), group_black_list_block()]))
async def repeateron(app: Ariadne, group: Group, message: MessageChain):

    if yaml_data['Saya']['Repeater']['Disabled']:
        return
    elif 'Repeater' in group_data[group.id]['DisabledFunc']:
        return
    elif yaml_data['Saya']['Repeater']['Random']['Disabled']:
        return

    saying = message.asDisplay()
    randint = random.randint(1, yaml_data['Saya']['Repeater']['Random']['Probability'])
    if randint == yaml_data['Saya']['Repeater']['Random']['Probability']:
        ifpic = not message.has(Image)
        ifface = not message.has(Face)
        ifat = not message.has(At)
        if ifpic & ifface & ifat:
            app.logger.info('已触发随机复读')
            repdict[group.id] = {'msg': saying, 'times': 1, 'last': saying}
            res = await text_moderation(saying)
            if res['Suggestion'] == "Pass":
                await app.sendGroupMessage(group, MessageChain.create([Plain(saying)]))
