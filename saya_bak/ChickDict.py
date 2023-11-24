import httpx

from graia.saya import Channel
from graia.ariadne.model import Group, Member
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, At, Image
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    RegexResult,
    WildcardMatch,
)

from config import yaml_data
from util.sendMessage import safeSendGroupMessage
from core_bak.control import Permission, Interval, Function

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    FullMatch("查梗"),
                    "anything" @ WildcardMatch(optional=True),
                ]
            )
        ],
        decorators=[
            Function.require("ChickDict"),
            Permission.require(),
            Interval.require(80),
        ],
    )
)
async def fun_dict(group: Group, member: Member, anything: RegexResult):
    if not anything.matched:
        await safeSendGroupMessage(group, MessageChain.create([Plain("用法：查梗 xxxxx")]))
    else:
        say_name = anything.result.asDisplay()
        if (
            yaml_data["Basic"]["Permission"]["MasterName"].replace(" ", "").upper()
            in say_name.replace(" ", "").upper()
            or yaml_data["Basic"]["BotName"].replace(" ", "").upper()
            in say_name.replace(" ", "").upper()
        ):
            return await safeSendGroupMessage(
                group, MessageChain.create([At(member.id), Plain(" 爬")])
            )

        api_url = "https://api.jikipedia.com/go/search_definitions"
        api_data = {"page": 1, "phrase": say_name}
        api_headers = {
            "Client": "web",
            "Content-Type": "application/json;charset=UTF-8",
            "Origin": "https://jikipedia.com",
        }
        async with httpx.AsyncClient() as client:
            r = await client.post(api_url, json=api_data, headers=api_headers)
        r_fun = r.json()

        if "size" not in r_fun:
            await safeSendGroupMessage(
                group,
                MessageChain.create(
                    [
                        Plain("API 访问错误"),
                    ]
                ),
            )
        elif r_fun["size"] == 0:
            await safeSendGroupMessage(
                group,
                MessageChain.create(
                    [
                        Plain(f"未找到相应词条：{say_name}"),
                    ]
                ),
            )
        else:
            for r_fun_data in r_fun["data"]:
                r_fun_title = r_fun_data["term"]["title"]
                if say_name == r_fun_title:
                    r_fun_tags = "标签：无"
                    r_fun_text = r_fun_data["plaintext"]
                    tags = []
                    tag_num = 0
                    for t in r_fun_data["tags"]:
                        tags.append(t["name"])
                        tag_num = tag_num + 1
                    if tag_num != 0:
                        r_fun_tags = "标签：" + " | ".join(tags)
                    msg_text = f"词条：{r_fun_title}\n{r_fun_tags}\n----------------------\n{r_fun_text}\n"
                    msg_chain = [Plain(msg_text)]
                    msg_chain.extend(
                        Image(url=image["full"]["path"]) for image in r_fun_data["images"]
                    )

                    msg_chain.append(
                        Plain(
                            "----------------------\n数据来源为小鸡词典\nhttps://jikipedia.com/\n"
                            "如果发现任何有问题的词条，与本 bot 无关，请前往小鸡词典官网反馈。"
                        )
                    )
                    await safeSendGroupMessage(group, MessageChain.create(msg_chain))
                    break
            else:
                r_fun_titles = []
                n = 1
                for r_fun_data in r_fun["data"]:
                    r_fun_titles.append(r_fun_data["term"]["title"])
                    if n > 20:
                        break
                    n += 1
                await safeSendGroupMessage(
                    str(group.id),
                    MessageChain.create(
                        [
                            Plain(f"未找到相应词条：{say_name}"),
                            Plain("\n你可能要找？\n --->" + "\n --->".join(r_fun_titles)),
                            Plain("\n数据来源为小鸡词典\nhttps://jikipedia.com/"),
                            Plain("\n如果发现任何有问题的词条，与本 bot 无关，请前往小鸡词典官网反馈。"),
                        ]
                    ),
                )
