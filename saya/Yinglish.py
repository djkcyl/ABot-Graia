import random

import jieba
import jieba.posseg as pseg

from graia.saya import Saya, Channel
from graia.application import GraiaMiraiApplication
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.event.messages import GroupMessage, Group
from graia.application.message.parser.literature import Literature
from graia.application.message.elements.internal import MessageChain, Source, Plain

from util.RestControl import rest_control
from util.limit import member_limit_check
from config import yaml_data, group_data, sendmsg

jieba.setLogLevel(20)

saya = Saya.current()
channel = Channel.current()


def _词转换(x, y, 淫乱度):
    if random.random() > 淫乱度:
        return x
    if x in {'，', '。'}:
        return '……'
    if x in {'!', '！'}:
        return '❤'
    if len(x) > 1 and random.random() < 0.5:
        return f'{x[0]}……{x}'
    else:
        if y == 'n' and random.random() < 0.5:
            x = '〇' * len(x)
        return f'……{x}'


def chs2yin(s, 淫乱度=0.5):
    return ''.join([_词转换(x, y, 淫乱度) for x, y in pseg.cut(s)])


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Literature("淫语")],
                            headless_decorators=[rest_control(), member_limit_check(15)]))
async def main(app: GraiaMiraiApplication, group: Group, message: MessageChain, source: Source):

    if yaml_data['Saya']['Yinglish']['Disabled']:
        return await sendmsg(app=app, group=group)
    elif 'Yinglish' in group_data[group.id]['DisabledFunc']:
        return await sendmsg(app=app, group=group)

    saying = message.asDisplay().split(" ", 1)
    if len(saying[1]) < 200:
        await app.sendGroupMessage(group, MessageChain.create([Plain(chs2yin(saying[1]))]), quote=source.id)
    else:
        await app.sendGroupMessage(group, MessageChain.create([Plain("文字过长")]), quote=source.id)
