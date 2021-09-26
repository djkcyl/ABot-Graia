import httpx

from graia.saya import Saya, Channel
from graia.application.group import Group
from graia.application import GraiaMiraiApplication
from graia.application.event.messages import GroupMessage
from graia.application.message.parser.kanata import Kanata
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.parser.signature import RegexMatch, OptionalParam
from graia.application.message.elements.internal import Image_NetworkAddress, MessageChain, Plain

from util.limit import group_limit_check
from util.RestControl import rest_control
from util.UserBlock import black_list_block
from config import yaml_data, group_data, sendmsg

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Kanata([RegexMatch("色图|涩图|瑟图|setu"),
                                                        OptionalParam(name="message")])],
                            headless_decorators=[group_limit_check(5), rest_control(), black_list_block()]))
async def main(app: GraiaMiraiApplication, group: Group, message: MessageChain):

    if yaml_data['Saya']['Pixiv']['Disabled']:
        return await sendmsg(app=app, group=group)
    elif 'Pixiv' in group_data[group.id]['DisabledFunc']:
        return await sendmsg(app=app, group=group)

    if message:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"http://a60.one:404/get/tags/{message.asDisplay().strip()}?num=1")
            res = r.json()
        if res.get('code', False) == 200:
            pic = res['data']['pic_list'][0]
            await app.sendGroupMessage(group, MessageChain.create([
                Plain(f"ID：{pic['pic']}"),
                Plain(f"\nNAME：{pic['name']}"),
                Image_NetworkAddress(pic['url'])
            ]))
        elif res.get('code', False) == 404:
            await app.sendGroupMessage(group, MessageChain.create([
                Plain("未找到相应tag的色图")
            ]))
        else:
            await app.sendGroupMessage(group, MessageChain.create([
                Plain("慢一点慢一点，别冲辣！")
            ]))
    else:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"http://a60.one:404/")
            res = r.json()
        if res.get('code', False) == 200:
            await app.sendGroupMessage(group, MessageChain.create([
                Plain(f"ID：{res['pic']}"),
                Plain(f"\nNAME：{res['name']}"),
                Image_NetworkAddress(res['url'])
            ]))
        else:
            await app.sendGroupMessage(group, MessageChain.create([
                Plain("慢一点慢一点，别冲辣！")
            ]))
