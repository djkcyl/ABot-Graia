import random

from graia.saya import Saya, Channel
from graia.application.event.mirai import *
from graia.application.event.messages import *
from graia.application import GraiaMiraiApplication
from graia.application.message.elements.internal import *
from graia.saya.builtins.broadcast.schema import ListenerSchema

from config import Config


saya = Saya.current()
channel = Channel.current()


repdict = {}

@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def repeater(app: GraiaMiraiApplication, group: Group, message: MessageChain):
    
    if Config.Saya.Repeater.Disabled:
        return
    elif group.id in Config.Saya.Repeater.Blacklist:
        return
    
    global repdict
    saying = message.asDisplay()
    ifpic = "[图片]" not in saying
    ifface = "[表情]" not in saying
    ifat = not message.has(At)
    if ifpic & ifface & ifat:
        if group.id not in repdict:
            repdict[group.id] = {'msg': saying, 'num': 1, 'last': ""}
        elif saying == repdict[group.id]['msg']:
            repdict[group.id]['num'] = repdict[group.id]['num'] + 1
            if repdict[group.id]['num'] == Config.Saya.Repeater.RepeatTimes and saying != repdict[group.id]['last']:
                await app.sendGroupMessage(group, MessageChain.create([Plain(saying)]))
                repdict[group.id] = {'msg': saying, 'num': 1, 'last': saying}
        else:
            repdict[group.id]['msg'] = saying
            repdict[group.id]['num'] = 1
            
@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def repeateron(app: GraiaMiraiApplication, group: Group, message: MessageChain):
    if Config.Saya.Repeater.Disabled:
        return
    elif group.id in Config.Saya.Repeater.Blacklist:
        return
    elif Config.Saya.Repeater.Random.Disabled:
        return
    
    saying = message.asDisplay()
    randint = random.randint(1, Config.Saya.Repeater.Random.Probability)
    if randint == Config.Saya.Repeater.Random.Probability:
        ifpic = "[图片]" not in saying
        ifface = "[表情]" not in saying
        ifat = not message.has(At)
        if ifpic & ifface & ifat:
            print('已触发随机复读')
            await app.sendGroupMessage(group, MessageChain.create([Plain(saying)]))