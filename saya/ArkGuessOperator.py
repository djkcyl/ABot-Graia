import httpx
import base64
import asyncio

from loguru import logger
from graia.saya import Saya, Channel
from graia.ariadne.model import Group, Member
from graia.broadcast.interrupt.waiter import Waiter
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.broadcast.interrupt import InterruptControl
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.element import Plain, Source, Voice, At
from graia.ariadne.message.parser.twilight import Twilight, RegexMatch

from database.db import add_answer
from util.sendMessage import safeSendGroupMessage
from util.control import Permission, Interval, Function

saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
inc = InterruptControl(bcc)

RUNNING = {}


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight({"ark": RegexMatch(r"(明日)?方舟猜干员")})],
        decorators=[
            Function.require("ArkGuessOperator"),
            Permission.require(),
            Interval.require(30),
        ],
    )
)
async def guess_operator(group: Group, source: Source):
    @Waiter.create_using_function(
        listening_events=[GroupMessage], using_decorators=[Permission.require()]
    )
    async def waiter1(
        waiter1_group: Group,
        waiter1_member: Member,
        waiter1_source: Source,
        waiter1_message: MessageChain,
    ):
        if waiter1_group.id == group.id:
            waiter1_saying = waiter1_message.asDisplay()
            if waiter1_saying == "取消":
                return False, False
            elif waiter1_saying == RUNNING[group.id]:
                return waiter1_member.id, waiter1_source

    if group.id in RUNNING:
        return
    else:
        RUNNING[group.id] = None

    async with httpx.AsyncClient() as client:
        resp = await client.get("http://a60.one:8009/random")
        operator_name = base64.b64decode(resp.headers["X-Operator-Name"]).decode(
            "utf-8"
        )
        operator_voice = resp.content

    logger.info(f"{group.name} 开始猜干员：{operator_name}")
    RUNNING[group.id] = operator_name

    await safeSendGroupMessage(group, MessageChain.create("正在抽取干员"), quote=source)
    await safeSendGroupMessage(
        group, MessageChain.create([Voice(data_bytes=operator_voice)])
    )

    try:
        result_member, result_source = await asyncio.wait_for(
            inc.wait(waiter1), timeout=60
        )
        if result_source:
            del RUNNING[group.id]
            await add_answer(str(result_member))
            await safeSendGroupMessage(
                group,
                MessageChain.create(
                    [
                        Plain(f"干员名称：{operator_name}\n恭喜 "),
                        At(result_member),
                        Plain(" 猜中了！"),
                    ]
                ),
                quote=result_source,
            )
        else:
            del RUNNING[group.id]
            await safeSendGroupMessage(group, MessageChain.create("已取消"))

    except asyncio.TimeoutError:
        del RUNNING[group.id]
        await safeSendGroupMessage(
            group,
            MessageChain.create([Plain(f"干员名称：{operator_name}\n没有人猜中，真可惜！")]),
            quote=source,
        )
