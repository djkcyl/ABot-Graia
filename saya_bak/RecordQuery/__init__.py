import json
import httpx
import asyncio

from graia.saya import Channel, Saya
from graia.ariadne.model import Group, Member
from graia.broadcast.interrupt.waiter import Waiter
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.broadcast.interrupt import InterruptControl
from graia.ariadne.message.element import At, Plain, Source
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    RegexResult,
    ElementMatch,
    ElementResult,
    WildcardMatch,
)

from util.sendMessage import safeSendGroupMessage
from core_bak.control import Function, Interval, Permission

from .draw_record_image import AUTH, DATABASE, draw_r6

saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
inc = InterruptControl(bcc)

BINDFILE = DATABASE.joinpath("bind.json")
if BINDFILE.exists():
    with BINDFILE.open("r") as f:
        bind = json.load(f)
else:
    with BINDFILE.open("w") as f:
        bind = {}
        json.dump(bind, f, indent=2)

WAITING = []


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    FullMatch("查战绩"),
                    FullMatch("r6"),
                    "at" @ ElementMatch(At, optional=True),
                    "name" @ WildcardMatch(optional=True),
                ]
            ),
        ],
        decorators=[
            Function.require("RecordQuery"),
            Permission.require,
            Interval.require(30),
        ],
    )
)
async def main(
    group: Group, member: Member, at: ElementResult, name: RegexResult, source: Source
):
    @Waiter.create_using_function(
        listening_events=[GroupMessage], using_decorators=[Permission.require()]
    )
    async def waiter1(
        waiter1_group: Group, waiter1_member: Member, waiter1_message: MessageChain
    ):
        if all([waiter1_group.id == group.id, waiter1_member.id == member.id]):
            waiter1_saying = waiter1_message.asDisplay()
            if waiter1_saying == "取消":
                return False
            elif waiter1_saying.replace(" ", "") == "":
                await safeSendGroupMessage(
                    group, MessageChain.create([Plain("请不要输入空格")])
                )
            else:
                return waiter1_saying

    @Waiter.create_using_function(
        listening_events=[GroupMessage], using_decorators=[Permission.require()]
    )
    async def confirm(
        confirm_group: Group,
        confirm_member: Member,
        confirm_message: MessageChain,
        confirm_source: Source,
    ):
        if all([confirm_group.id == group.id, confirm_member.id == member.id]):
            saying = confirm_message.asDisplay()
            if saying == "是":
                return True
            elif saying == "否":
                return False
            else:
                await safeSendGroupMessage(
                    group,
                    MessageChain.create([At(confirm_member.id), Plain("请发送是或否来进行确认")]),
                    quote=confirm_source,
                )

    if member.id not in WAITING:
        WAITING.append(member.id)

        if at.matched:
            atid = str(at.result.id)
            if atid not in bind:
                WAITING.remove(member.id)
                return await safeSendGroupMessage(
                    group, MessageChain.create([At(atid), Plain(" 暂未绑定账号")])
                )
            else:
                nick_name = bind[atid]
        elif name.matched:
            nick_name = name.result.asDisplay().strip()
        elif str(member.id) not in bind:
            # 等待输入昵称
            try:
                await safeSendGroupMessage(
                    group,
                    MessageChain.create(
                        "未绑定账号，请在一分钟内发送你的游戏昵称，不支持改绑，请谨慎填写，如需取消绑定请发送“取消”"
                    ),
                )
                nick_name = await asyncio.wait_for(inc.wait(waiter1), timeout=60)
                if not nick_name:
                    WAITING.remove(member.id)
                    return await safeSendGroupMessage(
                        group, MessageChain.create([Plain("已取消")])
                    )
            except asyncio.TimeoutError:
                WAITING.remove(member.id)
                return await safeSendGroupMessage(
                    group, MessageChain.create([Plain("等待超时")]), quote=source.id
                )

            # 搜索昵称
            async with httpx.AsyncClient(
                timeout=10, auth=AUTH, follow_redirects=True
            ) as client:
                resp = await client.get(
                    f"https://api.statsdb.net/r6/pc/player/{nick_name}"
                )
                player_data = resp.json()

            if resp.status_code == 200:
                # 询问是否绑定
                try:
                    confirm_wait = await safeSendGroupMessage(
                        group,
                        MessageChain.create(
                            Plain(
                                f"已搜索到用户：{player_data['payload']['user']['nickname']}"
                            ),
                            Plain(f"\nUUID：{player_data['payload']['user']['id']}"),
                            Plain("\n是否需要绑定此账号？"),
                        ),
                    )
                    if not await asyncio.wait_for(inc.wait(confirm), timeout=15):
                        WAITING.remove(member.id)
                        return await safeSendGroupMessage(
                            group, MessageChain.create("已取消")
                        )
                    else:
                        WAITING.remove(member.id)
                        bind[str(member.id)] = player_data["payload"]["user"][
                            "nickname"
                        ]
                        with BINDFILE.open("w", encoding="utf-8") as f:
                            json.dump(bind, f, indent=2)
                        return await safeSendGroupMessage(
                            group, MessageChain.create(f"绑定成功：{nick_name}，再次输入指令即可查询")
                        )
                except asyncio.TimeoutError:
                    WAITING.remove(member.id)
                    return await safeSendGroupMessage(
                        group,
                        MessageChain.create("等待超时"),
                        quote=confirm_wait.messageId,
                    )
            # 如果没搜索到
            elif resp.status_code == 404:
                WAITING.remove(member.id)
                return await safeSendGroupMessage(
                    group, MessageChain.create(f"未搜索到该昵称：{nick_name}")
                )
            # 如果其他错误
            else:
                WAITING.remove(member.id)
                return await safeSendGroupMessage(
                    group,
                    MessageChain.create(f"未知错误：{player_data['message']}"),
                )
        else:
            nick_name = bind[str(member.id)]

        await safeSendGroupMessage(group, MessageChain.create(f"正在查询：{nick_name}"))
        msg = await draw_r6(nick_name)
        await safeSendGroupMessage(group, MessageChain.create(msg), quote=source.id)
        WAITING.remove(member.id)
