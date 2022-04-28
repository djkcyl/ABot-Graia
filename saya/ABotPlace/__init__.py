import re
import asyncio

from graia.saya import Channel, Saya
from graia.ariadne.model import Group, Member
from graia.broadcast.interrupt.waiter import Waiter
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import GroupMessage
from graia.broadcast.interrupt import InterruptControl
from graia.ariadne.message.element import At, Image, Plain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    RegexMatch,
    RegexResult,
)

from config import COIN_NAME
from database.db import reduce_gold
from util.sendMessage import safeSendGroupMessage
from util.control import Function, Interval, Permission

from .database import fill_pixel
from .draw import get_draw_line, draw_pixel, merge_chunk, color_plant_img

saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
inc = InterruptControl(bcc)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [FullMatch("查看画板")],
            )
        ],
        decorators=[
            Function.require("ABotPlace"),
            Permission.require(),
            Interval.require(30),
        ],
    )
)
async def vive_full_image(group: Group):
    await safeSendGroupMessage(
        group, MessageChain.create(Image(data_bytes=merge_chunk()))
    )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [FullMatch("画板作画")],
            )
        ],
        decorators=[
            Function.require("ABotPlace"),
            Permission.require(),
            Interval.require(30),
        ],
    )
)
async def place_draw(group: Group, member: Member):
    @Waiter.create_using_function(
        listening_events=[GroupMessage], using_decorators=[Permission.require()]
    )
    async def waiter_chunk(
        waiter1_group: Group, waiter1_member: Member, waiter1_message: MessageChain
    ):
        if waiter1_group.id == group.id and waiter1_member.id == member.id:
            if waiter1_message.asDisplay() == "取消":
                return False
            else:
                p = re.compile(r"^(\d{1,2})[|;:,，\s](\d{1,2})$")
                if p.match(waiter1_message.asDisplay()):
                    x, y = p.match(waiter1_message.asDisplay()).groups()
                    if 31 >= int(x) >= 0 and 31 >= int(y) >= 0:
                        return int(x), int(y)
                    else:
                        await safeSendGroupMessage(
                            waiter1_group,
                            MessageChain.create(
                                At(waiter1_member),
                                Plain("坐标超出范围（0-31），请重新输入"),
                            ),
                        )
                else:
                    await safeSendGroupMessage(
                        waiter1_group,
                        MessageChain.create(
                            At(waiter1_member),
                            Plain("请输入正确的坐标，格式：x,y"),
                        ),
                    )

    @Waiter.create_using_function(
        listening_events=[GroupMessage], using_decorators=[Permission.require()]
    )
    async def waiter_color(
        waiter1_group: Group, waiter1_member: Member, waiter1_message: MessageChain
    ):
        if waiter1_group.id == group.id and waiter1_member.id == member.id:
            if waiter1_message.asDisplay() == "取消":
                return False
            else:
                p = re.compile(r"^(\d{1,2})$")
                if p.match(waiter1_message.asDisplay()):
                    color = int(waiter1_message.asDisplay())
                    print(color)
                    if 32 >= color >= 1:
                        return int(color)
                    else:
                        await safeSendGroupMessage(
                            waiter1_group,
                            MessageChain.create(
                                At(waiter1_member),
                                Plain(" 颜色超出范围（0-31），请重新输入"),
                            ),
                        )

    await safeSendGroupMessage(
        group,
        MessageChain.create(
            At(member), Plain(" 请发送想要作画的区块坐标：\n"), Image(data_bytes=get_draw_line())
        ),
    )

    try:
        chunk = await asyncio.wait_for(inc.wait(waiter_chunk), 60)
        if chunk:
            chunk_x, chunk_y = chunk
            await safeSendGroupMessage(
                group,
                MessageChain.create(
                    At(member),
                    Plain(" 请输入想要绘制的像素坐标：\n"),
                    Image(data_bytes=get_draw_line(chunk_x, chunk_y)),
                ),
            )
            pixel = await asyncio.wait_for(inc.wait(waiter_chunk), 60)
            if pixel:
                pixel_x, pixel_y = pixel
                await safeSendGroupMessage(
                    group,
                    MessageChain.create(
                        At(member),
                        Plain(" 请输入想要绘制的颜色：\n"),
                        Image(data_bytes=color_plant_img),
                    ),
                )
                color = await asyncio.wait_for(inc.wait(waiter_color), 60)
                if color:
                    if await reduce_gold(str(member.id), 1):
                        fill_id = fill_pixel(
                            member, group, color, chunk_x, chunk_y, pixel_x, pixel_y
                        )
                        draw_pixel(chunk_x, chunk_y, pixel_x, pixel_y, color)
                        await safeSendGroupMessage(
                            group,
                            MessageChain.create(
                                f"ID: {fill_id} 绘制成功\n",
                                Image(data_bytes=get_draw_line(chunk_x, chunk_y)),
                            ),
                        )
                    else:
                        await safeSendGroupMessage(
                            group,
                            MessageChain.create(
                                At(member), Plain(f"，你的{COIN_NAME}不足，无法绘制")
                            ),
                        )
            else:
                await safeSendGroupMessage(
                    group, MessageChain.create(At(member), Plain(" 操作已取消"))
                )
                return

        else:
            await safeSendGroupMessage(
                group, MessageChain.create(At(member), Plain(" 操作已取消"))
            )
            return

    except asyncio.TimeoutError:
        await safeSendGroupMessage(
            group,
            MessageChain.create(At(member), Plain(" 等待超时，操作已取消")),
        )
        return


# 快捷绘制
@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    FullMatch("快捷作画"),
                    "coordinates"
                    @ RegexMatch(
                        r"(\d{1,2})[|;:,，\s](\d{1,2})[|;:,，\s](\d{1,2})[|;:,，\s](\d{1,2})[|;:,，\s](\d{1,2})$"
                    ),
                ],
            )
        ],
        decorators=[
            Function.require("ABotPlace"),
            Permission.require(),
            Interval.require(10),
        ],
    )
)
async def fast_place(group: Group, member: Member, coordinates: RegexResult):
    p = re.compile(
        r"^(\d{1,2})[|;:,，\s](\d{1,2})[|;:,，\s](\d{1,2})[|;:,，\s](\d{1,2})[|;:,，\s](\d{1,2})$"
    )
    coordinate = p.match(coordinates.result.asDisplay())
    chunk_x, chunk_y, pixel_x, pixel_y, color = coordinate.groups()
    chunk_x, chunk_y, pixel_x, pixel_y, color = (
        int(chunk_x),
        int(chunk_y),
        int(pixel_x),
        int(pixel_y),
        int(color),
    )

    if (
        31 >= chunk_x >= 0
        and 31 >= chunk_y >= 0
        and 31 >= pixel_x >= 0
        and 31 >= pixel_y >= 0
        and 32 >= color >= 1
    ):
        if await reduce_gold(str(member.id), 1):
            fill_id = fill_pixel(member, group, color, chunk_x, chunk_y, pixel_x, pixel_y)
            draw_pixel(chunk_x, chunk_y, pixel_x, pixel_y, color)
            await safeSendGroupMessage(
                group,
                MessageChain.create(
                    f"ID: {fill_id} 绘制成功\n",
                    Image(data_bytes=get_draw_line(chunk_x, chunk_y)),
                ),
            )
        else:
            await safeSendGroupMessage(
                group,
                MessageChain.create(At(member), Plain(f"，你的{COIN_NAME}不足，无法绘制")),
            )
    else:
        await safeSendGroupMessage(
            group, MessageChain.create(At(member), Plain(" 你输入的数值错误，无法绘制，请检查后重发"))
        )
