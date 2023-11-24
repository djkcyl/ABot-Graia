import re
import asyncio

from loguru import logger
from graia.saya import Channel, Saya
from graia.ariadne.model import Group, Member
from graia.broadcast.interrupt.waiter import Waiter
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.broadcast.interrupt import InterruptControl
from graia.ariadne.message.element import Image, Source
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    RegexMatch,
    ElementMatch,
    ElementResult,
)

from util.ocr import OCR
from util.sendMessage import safeSendGroupMessage
from core_bak.control import Function, Interval, Permission

from .data import recruit_data
from .recruit_calc import calculate
from .draw_recruit_image import draw

MEMBER_RUNING_LIST = []
saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
inc = InterruptControl(bcc)
known_tags = set(y for x in recruit_data for y in x[2])
known_tags.update(("资深干员", "高级资深干员"))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    "head" @ RegexMatch(r"公招识别|查公招"),
                    "enter" @ FullMatch("\n", optional=True),
                    "image" @ ElementMatch(Image, optional=True),
                ]
            )
        ],
        decorators=[
            Function.require("ArkRecruit"),
            Permission.require(),
            Interval.require(30),
        ],
    )
)
async def recruit(
    member: Member,
    group: Group,
    image: ElementResult,
    source: Source,
):
    @Waiter.create_using_function(
        listening_events=[GroupMessage], using_decorators=[Permission.require()]
    )
    async def image_waiter(
        waiter1_group: Group, waiter1_member: Member, waiter1_message: MessageChain
    ):
        if waiter1_group.id == group.id and waiter1_member.id == member.id:
            if waiter1_message.has(Image):
                return await waiter1_message.getFirst(Image).get_bytes()
            else:
                return False

    if member.id in MEMBER_RUNING_LIST:
        return
    else:
        MEMBER_RUNING_LIST.append(member.id)

    if image.matched:
        image_data = await image.result.get_bytes()
    else:
        await safeSendGroupMessage(
            group, MessageChain.create("请发送要识别的图片"), quote=source
        )
        try:
            image_data = await asyncio.wait_for(inc.wait(image_waiter), 30)
            if not image_data:
                MEMBER_RUNING_LIST.remove(member.id)
                return await safeSendGroupMessage(
                    group, MessageChain.create("你发送的不是“一张”图片，请重试"), quote=source
                )
        except asyncio.TimeoutError:
            MEMBER_RUNING_LIST.remove(member.id)
            return await safeSendGroupMessage(
                group, MessageChain.create("图片等待超时"), quote=source
            )

    ocr = OCR(image_data)
    ocr_result = await ocr.ocr()

    tags = []
    p = re.compile(r".击干员")
    for i in ocr_result["result"]:
        if p.search(i):
            tags.append("狙击干员")
        elif i in known_tags:
            tags.append(i)
    p = re.compile(r"高级.*")
    for i in ocr_result["result"]:
        if p.search(i) and "高级资深干员" not in tags:
            tags.append("高级资深干员")

    if len(tags) == 0:
        msg = ["未识别到标签"]
    else:
        logger.info(f"[明日方舟公招识别] 识别到的标签：{'，'.join(tags)}")
        recruilt_data = draw(calculate(tags))
        if recruilt_data:
            msg = [f"识别结果：{'，'.join(tags)}", Image(data_bytes=recruilt_data)]

        else:
            msg = [f"识别结果：{'，'.join(tags)}\n未包含有意义的组合"]

    await safeSendGroupMessage(
        group,
        MessageChain.create(msg),
        quote=source,
    )
    MEMBER_RUNING_LIST.remove(member.id)
