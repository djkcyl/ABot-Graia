import httpx
import asyncio

from datetime import datetime
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.model import Group, Member, MemberPerm
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import Twilight, Sparkle
from graia.ariadne.message.parser.pattern import FullMatch, RegexMatch
from graia.ariadne.message.element import ForwardNode, Image, Plain, Forward

from config import yaml_data, group_data
from util.sendMessage import safeSendGroupMessage
from util.control import Permission, Interval, Rest

saya = Saya.current()
channel = Channel.current()


class PixivSparkle(Sparkle):
    tag1 = RegexMatch(r".*", optional=True)
    header = FullMatch("涩图")
    tag2 = RegexMatch(r".*", optional=True)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(PixivSparkle)],
        decorators=[Rest.rest_control(), Permission.require(), Interval.require()],
    )
)
async def main(app: Ariadne, group: Group, member: Member, sparkle: Sparkle):

    if (
        yaml_data["Saya"]["Pixiv"]["Disabled"]
        and group.id != yaml_data["Basic"]["Permission"]["DebugGroup"]
    ):
        return
    elif "Pixiv" in group_data[str(group.id)]["DisabledFunc"]:
        return

    if yaml_data["Saya"]["Pixiv"]["san"] == "r18":
        san = 6
    elif yaml_data["Saya"]["Pixiv"]["san"] == "r16":
        san = 4
    else:
        san = 2

    saying: PixivSparkle = sparkle

    if saying.tag1.matched or saying.tag2.matched:
        tag = (
            saying.tag1.result.getFirst(Plain).text
            if saying.tag1.matched
            else saying.tag2.result.getFirst(Plain).text
        )
        async with httpx.AsyncClient() as client:
            r = await client.get(f"http://a60.one:404/get/tags/{tag}?num=5&san={san}")
            res = r.json()
        if res.get("code", False) == 200:
            if yaml_data["Saya"]["Pixiv"]["Forward"]:
                if member.permission == MemberPerm.Owner:
                    name = "群主"
                elif member.permission == MemberPerm.Administrator:
                    name = "管理员"
                elif member.permission == MemberPerm.Member:
                    name = "高层群员"

                forwardnode = [
                    ForwardNode(
                        senderId=member.id,
                        time=datetime.now(),
                        senderName=member.name,
                        messageChain=MessageChain.create(
                            f"我是发涩图的{name}，请大家坐稳扶好，涩图要来咯！"
                        ),
                    )
                ]
                for pic in res["data"]["imgs"]:
                    forwardnode.append(
                        ForwardNode(
                            senderId=member.id,
                            time=datetime.now(),
                            senderName=member.name,
                            messageChain=MessageChain.create(
                                [
                                    Plain(f"ID：{pic['pic']}\n"),
                                    Plain(f"NAME：{pic['name']}\n"),
                                    Plain(f"SAN: {pic['sanity_level']}\n"),
                                    Image(url=pic["url"]),
                                ]
                            ),
                        )
                    )
                message = MessageChain.create(Forward(nodeList=forwardnode))
            else:
                pic = res["data"]["imgs"][0]
                message = MessageChain.create(
                    [
                        Plain(f"ID：{pic['pic']}\n"),
                        Plain(f"NAME：{pic['name']}\n"),
                        Plain(f"SAN: {pic['sanity_level']}\n"),
                        Image(url=pic["url"]),
                    ]
                )

            msg = await safeSendGroupMessage(group, message)
            if yaml_data["Saya"]["Pixiv"]["Recall"]:
                await asyncio.sleep(
                    yaml_data["Saya"]["Pixiv"]["Interval"]
                    if yaml_data["Saya"]["Pixiv"]["Interval"] < 110
                    else 110
                )
                await app.recallMessage(msg)
        elif res.get("code", False) == 404:
            await safeSendGroupMessage(
                group, MessageChain.create([Plain("未找到相应tag的色图")])
            )
        else:
            await safeSendGroupMessage(
                group, MessageChain.create([Plain("慢一点慢一点，别冲辣！")])
            )
    else:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"http://a60.one:404/?num=5&san={san}")
            res = r.json()
        if res.get("code", False) == 200:
            if yaml_data["Saya"]["Pixiv"]["Forward"]:
                if member.permission == MemberPerm.Owner:
                    name = "群主"
                elif member.permission == MemberPerm.Administrator:
                    name = "管理员"
                elif member.permission == MemberPerm.Member:
                    name = "高层群员"

                forwardnode = [
                    ForwardNode(
                        senderId=member.id,
                        time=datetime.now(),
                        senderName=member.name,
                        messageChain=MessageChain.create(
                            f"我是发涩图的{name}，请大家坐稳扶好，涩图要来咯！"
                        ),
                    )
                ]
                for pic in res["data"]["imgs"]:
                    forwardnode.append(
                        ForwardNode(
                            senderId=member.id,
                            time=datetime.now(),
                            senderName=member.name,
                            messageChain=MessageChain.create(
                                [
                                    Plain(f"ID：{pic['pic']}\n"),
                                    Plain(f"NAME：{pic['name']}\n"),
                                    Plain(f"SAN: {pic['sanity_level']}\n"),
                                    Image(url=pic["url"]),
                                ]
                            ),
                        )
                    )
                message = MessageChain.create(Forward(nodeList=forwardnode))
            else:
                pic = res["data"]["imgs"][0]
                message = MessageChain.create(
                    [
                        Plain(f"ID：{pic['pic']}\n"),
                        Plain(f"NAME：{pic['name']}\n"),
                        Plain(f"SAN: {pic['sanity_level']}\n"),
                        Image(url=pic["url"]),
                    ]
                )
            msg = await safeSendGroupMessage(group, message)
            if yaml_data["Saya"]["Pixiv"]["Recall"]:
                await asyncio.sleep(
                    yaml_data["Saya"]["Pixiv"]["Interval"]
                    if yaml_data["Saya"]["Pixiv"]["Interval"] < 110
                    else 110
                )
                await app.recallMessage(msg)
        else:
            await safeSendGroupMessage(
                group, MessageChain.create([Plain("慢一点慢一点，别冲辣！")])
            )
