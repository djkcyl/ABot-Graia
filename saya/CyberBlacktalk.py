import json
import httpx

from graia.application import GraiaMiraiApplication
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.event.messages import *
from graia.application.event.mirai import *
from graia.application.message.elements.internal import *
from graia.application.message.parser.literature import Literature

from config import yaml_data, group_data, sendmsg


saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("你在说什么")]))
async def what_are_you_saying(app: GraiaMiraiApplication, group: Group, member: Member, message: MessageChain):  # 你在说什么

    if yaml_data['Saya']['CyberBlacktalk']['Disabled']:
        return await sendmsg(app=app, group=group)
    elif 'CyberBlacktalk' in group_data[group.id]['DisabledFunc']:
        return await sendmsg(app=app, group=group)

    saying = message.asDisplay().split()
    if len(saying) != 2:
        return await app.sendGroupMessage(group, MessageChain.create([Plain(f"你在说什么 <需要翻译的简写>")]))
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
        return await app.sendGroupMessage(group, MessageChain.create([Plain(f"你在说什么 <需要翻译的简写>")]))
    if "trans" in tb[0] and len(tb[0]["trans"]) != 0:
        tc = tb[0]["trans"]
        td = f"{saying[1]} 可能是：\n" + "\n".join(tc)
    elif "inputting" in tb[0] and len(tb[0]["inputting"]) != 0:
        tc = tb[0]["inputting"]
        td = f"{saying[1]} 可能是：\n" + "\n".join(tc)
    else:
        td = f"未收录该条目"

    await app.sendGroupMessage(group, MessageChain.create([
        At(member.id),
        Plain(f"\n{td}")
    ]))
