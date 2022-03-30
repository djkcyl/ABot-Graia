import json
import httpx

from graia.saya import Channel
from graia.ariadne.model import Group, Member
from graia.ariadne.message.element import Plain, At
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    RegexResult,
    WildcardMatch,
)

from util.sendMessage import safeSendGroupMessage
from util.control import Permission, Interval, Function

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    FullMatch("能不能好好说话"),
                    "anything" @ WildcardMatch(optional=True),
                ]
            )
        ],
        decorators=[
            Function.require("CyberBlacktalk"),
            Permission.require(),
            Interval.require(),
        ],
    )
)
async def what_are_you_saying(group: Group, member: Member, anything: RegexResult):
    if anything.matched:
        api_url = "https://lab.magiconch.com/api/nbnhhsh/guess"
        api_data = {"text": anything.result.asDisplay()}
        api_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/51.0.2704.103 Safari/537.36"
        }
        translation = httpx.post(api_url, json=api_data, headers=api_headers)
        ta = translation.text
        tb = json.loads(ta)
        if len(tb) == 0:
            return await safeSendGroupMessage(
                group, MessageChain.create("用法：能不能好好说话 <需要翻译的简写>")
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
        await safeSendGroupMessage(group, MessageChain.create("用法：能不能好好说话 <需要翻译的简写>"))
