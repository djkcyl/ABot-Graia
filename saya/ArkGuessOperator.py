import httpx
import base64
import asyncio

from loguru import logger
from graia.saya import Saya, Channel
from graia.ariadne.model import Group
from graia.broadcast.interrupt.waiter import Waiter
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.broadcast.interrupt import InterruptControl
from graia.ariadne.message.parser.pattern import FullMatch
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.element import Plain, Source, Voice, At
from graia.ariadne.message.parser.twilight import Twilight, Sparkle

from database.db import add_answer
from config import yaml_data, group_data
from util.control import Permission, Interval
from util.sendMessage import safeSendGroupMessage

saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
inc = InterruptControl(bcc)

RUNNING = {}


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(Sparkle([FullMatch("明日", optional=True), FullMatch("方舟猜干员")]))
        ],
        decorators=[Permission.require(), Interval.require(30)],
    )
)
async def guess_operator(group: Group, source: Source):

    if (
        yaml_data["Saya"]["ArkGuessOperator"]["Disabled"]
        and group.id != yaml_data["Basic"]["Permission"]["DebugGroup"]
    ):
        return
    elif "ArkGuessOperator" in group_data[str(group.id)]["DisabledFunc"]:
        return

    @Waiter.create_using_function([GroupMessage])
    async def waiter1(
        waiter1_group: Group, waiter1_event: GroupMessage, waiter1_message: MessageChain
    ):
        if waiter1_group.id == group.id:
            waiter1_saying = waiter1_message.asDisplay()
            if waiter1_saying == "取消":
                return False
            elif waiter1_saying == RUNNING[group.id]:
                return waiter1_event

    if group.id in RUNNING:
        return

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
        guess_operator_result = await asyncio.wait_for(inc.wait(waiter1), timeout=60)
        if guess_operator_result:
            del RUNNING[group.id]
            await add_answer(str(guess_operator_result))
            await safeSendGroupMessage(
                group,
                MessageChain.create(
                    [
                        Plain(f"干员名称：{operator_name}\n恭喜 "),
                        At(guess_operator_result.sender.id),
                        Plain(" 猜中了！"),
                    ]
                ),
                quote=guess_operator_result.messageChain.getFirst(Source),
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
