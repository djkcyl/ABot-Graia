import random

from graia.saya import Saya, Channel
from graia.application.group import Group
from graia.application import GraiaMiraiApplication
from graia.application.event.messages import GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.elements.internal import MessageChain, Plain, At

from config import yaml_data, group_data


saya = Saya.current()
channel = Channel.current()


repdict = {}


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def repeater(app: GraiaMiraiApplication, group: Group, message: MessageChain):

    if yaml_data['Saya']['Repeater']['Disabled']:
        return
    elif 'Repeater' in group_data[group.id]['DisabledFunc']:
        return

    global repdict
    saying = message.asDisplay()
    ifpic = "[图片]" not in saying
    ifface = "[表情]" not in saying
    ifat = not message.has(At)
    if ifpic & ifface & ifat:
        if group.id not in repdict:
            repdict[group.id] = {'msg': saying, 'times': 1, 'last': ""}
        elif saying == repdict[group.id]['msg']:
            repdict[group.id]['times'] = repdict[group.id]['times'] + 1
            if repdict[group.id]['times'] == yaml_data['Saya']['Repeater']['RepeatTimes'] and saying != repdict[group.id]['last']:
                await app.sendGroupMessage(group, MessageChain.create([Plain(saying)]))
                repdict[group.id] = {'msg': saying, 'times': 1, 'last': saying}
        else:
            repdict[group.id]['msg'] = saying
            repdict[group.id]['times'] = 1


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def repeateron(app: GraiaMiraiApplication, group: Group, message: MessageChain):
    if yaml_data['Saya']['Repeater']['Disabled']:
        return
    elif 'Repeater' in group_data[group.id]['DisabledFunc']:
        return
    elif yaml_data['Saya']['Repeater']['Random']['Disabled']:
        return

    saying = message.asDisplay()
    randint = random.randint(1, yaml_data['Saya']['Repeater']['Random']['Probability'])
    if randint == yaml_data['Saya']['Repeater']['Random']['Probability']:
        ifpic = "[图片]" not in saying
        ifface = "[表情]" not in saying
        ifat = not message.has(At)
        if ifpic & ifface & ifat:
            print('已触发随机复读')
            await app.sendGroupMessage(group, MessageChain.create([Plain(saying)]))
