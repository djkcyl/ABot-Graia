import httpx

from graia.saya import Saya, Channel
from graia.ariadne.model import Group, Member
from graia.ariadne.message.element import Plain, At
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import Twilight, FullMatch, WildcardMatch

from util.sendMessage import safeSendGroupMessage
from util.TextModeration import text_moderation_async
from util.control import Permission, Interval, Rest, Function

saya = Saya.current()
channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                {
                    "head": FullMatch("/emoji"),
                    "anythings": WildcardMatch(optional=True),
                }
            )
        ],
        decorators=[
            Function.require("ChickEmoji"),
            Permission.require(),
            Rest.rest_control(),
            Interval.require(30),
        ],
    )
)
async def fun_dict(group: Group, member: Member, anythings: WildcardMatch):
    if anythings.matched:

        saying = anythings.result.asDisplay()
        api_url = "https://api.jikipedia.com/go/translate_plaintext"
        api_data = {"content": saying}
        api_headers = {
            "Client": "web",
            "Content-Type": "application/json;charset=UTF-8",
            "Origin": "https://jikipedia.com",
        }
        async with httpx.AsyncClient() as client:
            r = await client.post(api_url, json=api_data, headers=api_headers)
        emoji = r.json()
        moderation = await text_moderation_async(emoji["translation"])
        if moderation["status"]:
            await safeSendGroupMessage(
                group,
                MessageChain.create(
                    [At(member.id), Plain("\n" + emoji["translation"])]
                ),
            )
    else:
        await safeSendGroupMessage(group, MessageChain.create("用法：/emoji [文字]"))
