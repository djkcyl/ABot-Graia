import httpx

from graia.saya import Saya, Channel
from graia.ariadne.model import Group
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Plain
from graia.ariadne.message.parser.literature import Literature
from graia.saya.builtins.broadcast.schema import ListenerSchema

from config import yaml_data, group_data
from util.limit import group_limit_check
from util.RestControl import rest_control
from util.UserBlock import group_black_list_block

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Literature("涩图")],
                            headless_decorators=[group_limit_check(5), rest_control(), group_black_list_block()]))
async def main(app: Ariadne, group: Group, message: MessageChain):

    if yaml_data['Saya']['Pixiv']['Disabled']:
        return
    elif 'Pixiv' in group_data[group.id]['DisabledFunc']:
        return

    saying = message.asDisplay().split(" ", 1)

    if len(saying) == 1:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"http://a60.one:404/get/tags/{saying[1].strip()}?num=1")
            res = r.json()
        if res.get('code', False) == 200:
            pic = res['data']['pic_list'][0]
            await app.sendGroupMessage(group, MessageChain.create([
                Plain(f"ID：{pic['pic']}"),
                Plain(f"\nNAME：{pic['name']}"),
                Image(url=pic['url'])
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
                Image(url=res['url'])
            ]))
        else:
            await app.sendGroupMessage(group, MessageChain.create([
                Plain("慢一点慢一点，别冲辣！")
            ]))
