import json
import httpx

from graia.saya import Saya, Channel
from graia.ariadne.model import Group, Member
from graia.ariadne.message.element import Plain, At
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import Twilight, FullMatch, WildcardMatch

from config import yaml_data, group_data
from util.sendMessage import safeSendGroupMessage
from util.control import Permission, Interval, Rest

saya = Saya.current()
channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                {
                    "head": FullMatch("你在说什么"),
                    "anything": WildcardMatch(optional=True),
                }
            )
        ],
        decorators=[Rest.rest_control(), Permission.require(), Interval.require()],
    )
)
async def what_are_you_saying(group: Group, member: Member, anything: WildcardMatch):

    if (
        yaml_data["Saya"]["CyberBlacktalk"]["Disabled"]
        and group.id != yaml_data["Basic"]["Permission"]["DebugGroup"]
    ):
        return
    elif "CyberBlacktalk" in group_data[str(group.id)]["DisabledFunc"]:
        return

    if anything.matched:
        saying = anything.result.asDisplay()
        api_url = "https://lab.magiconch.com/api/nbnhhsh/guess"
        api_data = {"text": saying[1]}
        api_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/51.0.2704.103 Safari/537.36"
        }
        translation = httpx.post(api_url, json=api_data, headers=api_headers)
        ta = translation.text
        tb = json.loads(ta)
        if len(tb) == 0:
            return await safeSendGroupMessage(
                group, MessageChain.create("用法：能不能好好说话 [需要翻译的简写]")
            )

        msg = [At(member.id)]
        for dict in tb:
            if "trans" in dict and len(dict["trans"]) != 0:
                name = dict["name"]
                tc = dict["trans"]
                msg.append(
                    Plain(
                        f"\n===================\n{name} 可能是：\n  > " + "\n  > ".join(tc)
                    )
                )
            elif "inputting" in dict and len(dict["inputting"]) != 0:
                name = dict["name"]
                tc = dict["inputting"]
                msg.append(
                    Plain(
                        f"\n===================\n{name} 可能是：\n  > " + "\n  > ".join(tc)
                    )
                )
            else:
                msg.append(Plain("未收录该条目"))

        await safeSendGroupMessage(group, MessageChain.create(msg))
    else:

        await safeSendGroupMessage(group, MessageChain.create("用法：能不能好好说话 [需要翻译的简写]"))
