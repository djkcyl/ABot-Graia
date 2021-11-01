import json
import httpx

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group, Member
from graia.ariadne.message.element import Plain, At
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.parser.literature import Literature
from graia.saya.builtins.broadcast.schema import ListenerSchema

from config import yaml_data, group_data
from util.limit import member_limit_check
from util.RestControl import rest_control
from util.UserBlock import group_black_list_block

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Literature("你在说什么")],
                            headless_decorators=[rest_control(), member_limit_check(30), group_black_list_block()]))
async def what_are_you_saying(app: Ariadne, group: Group, member: Member, message: MessageChain):  # 你在说什么

    if yaml_data['Saya']['CyberBlacktalk']['Disabled']:
        return
    elif 'CyberBlacktalk' in group_data[group.id]['DisabledFunc']:
        return

    saying = message.asDisplay().split(" ", 1)
    if len(saying) != 2:
        return await app.sendGroupMessage(group, MessageChain.create([Plain(f"用法：你在说什么 <需要翻译的简写>")]))
    api_url = "https://lab.magiconch.com/api/nbnhhsh/guess"
    api_data = {"text": saying[1]}
    api_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/51.0.2704.103 Safari/537.36"}
    translation = httpx.post(api_url,
                             json=api_data,
                             headers=api_headers)
    ta = translation.text
    tb = json.loads(ta)
    if len(tb) == 0:
        return await app.sendGroupMessage(group, MessageChain.create([Plain(f"用法：你在说什么 <需要翻译的简写>")]))

    msg = [At(member.id)]
    for dict in tb:
        if "trans" in dict and len(dict["trans"]) != 0:
            name = dict["name"]
            tc = dict["trans"]
            msg.append(Plain(f"\n===================\n{name} 可能是：\n  > " + "\n  > ".join(tc)))
        elif "inputting" in dict and len(dict["inputting"]) != 0:
            name = dict["name"]
            tc = dict["inputting"]
            msg.append(Plain(f"\n===================\n{name} 可能是：\n  > " + "\n  > ".join(tc)))
        else:
            msg.append(Plain(f"未收录该条目"))

    await app.sendGroupMessage(group, MessageChain.create(msg))
