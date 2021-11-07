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
from util.sendMessage import selfSendGroupMessage
from util.control import Permission, Interval, Rest

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Literature("你在说什么")],
                            decorators=[Rest.rest_control(), Permission.require(), Interval.require()]))
async def what_are_you_saying(app: Ariadne, group: Group, member: Member, message: MessageChain):

    if yaml_data['Saya']['CyberBlacktalk']['Disabled']:
        return
    elif 'CyberBlacktalk' in group_data[str(group.id)]['DisabledFunc']:
        return

    saying = message.asDisplay().split(" ", 1)
    if len(saying) != 2:
        return await selfSendGroupMessage(group, MessageChain.create([Plain("用法：你在说什么 <需要翻译的简写>")]))
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
        return await selfSendGroupMessage(group, MessageChain.create([Plain("用法：你在说什么 <需要翻译的简写>")]))

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
            msg.append(Plain("未收录该条目"))

    await selfSendGroupMessage(group, MessageChain.create(msg))
