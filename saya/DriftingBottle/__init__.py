import re
import time
import httpx
import asyncio
import numpy as np

from io import BytesIO
from pathlib import Path
from loguru import logger
from pyzbar import pyzbar
from PIL import Image as IMG
from graia.saya import Channel, Saya
from graia.ariadne.model import Group, Member
from graia.broadcast.interrupt.waiter import Waiter
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import GroupMessage
from graia.broadcast.interrupt import InterruptControl
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.element import At, Image, Plain, Quote, Source
from graia.ariadne.message.parser.twilight import (
    Twilight,
    ArgResult,
    FullMatch,
    RegexMatch,
    RegexResult,
    ElementMatch,
    ArgumentMatch,
    WildcardMatch,
)

from database.db import reduce_gold
from util.text2image import create_image
from util.sendMessage import safeSendGroupMessage
from util.TextModeration import text_moderation_async
from util.ImageModeration import image_moderation_async
from util.control import Function, Interval, Permission
from config import COIN_NAME, save_config, user_list, yaml_data

from .db import (
    get_bottle,
    throw_bottle,
    clear_bottle,
    count_bottle,
    delete_bottle,
    get_my_bottles,
    get_bottle_by_id,
    add_bottle_score,
    add_bottle_discuss,
    get_bottle_discuss,
    get_bottle_score_avg,
)

saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
inc = InterruptControl(bcc)

IMAGE_PATH = Path(__file__).parent.joinpath("image")
IMAGE_PATH.mkdir(exist_ok=True)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    RegexMatch(r"^(扔|丢)(漂流瓶|瓶子)|pdb"),
                    "arg_reg_pic" @ RegexMatch(r"-P|-p|--pic", optional=True),
                    "arg_pic"
                    @ ArgumentMatch(
                        "-p", "-P", "--pic", action="store_true", optional=True
                    ),
                    "skip_review"
                    @ ArgumentMatch(
                        "-s",
                        "--skip-review",
                        action="store_true",
                        optional=True,
                        default=False,
                    ),
                    FullMatch("\n", optional=True),
                    "anythings1" @ WildcardMatch(optional=True),
                ],
            )
        ],
        decorators=[
            Function.require("DriftingBottle"),
            Permission.require(),
            Interval.require(30),
        ],
    )
)
async def throw_bottle_handler(
    group: Group,
    member: Member,
    source: Source,
    arg_pic: ArgResult,
    arg_reg_pic: RegexResult,
    skip_review: ArgResult,
    anythings1: RegexResult,
):
    @Waiter.create_using_function(
        listening_events=[GroupMessage], using_decorators=[Permission.require()]
    )
    async def image_waiter(
        waiter1_group: Group, waiter1_member: Member, waiter1_message: MessageChain
    ):
        if waiter1_group.id == group.id and waiter1_member.id == member.id:
            if waiter1_message.has(Image):
                return waiter1_message.getFirst(Image).url
            else:
                return False

    saying = anythings1
    text = None
    image_name = None
    image_url = None
    if saying.matched:
        message_chain = saying.result
        if message_chain.has(Plain):
            text = (
                MessageChain.create(message_chain.get(Plain))
                .merge(True)
                .asDisplay()
                .strip()
            )
            if text:
                for i in ["magnet:", "http"]:
                    if i in text:
                        return await safeSendGroupMessage(
                            group, MessageChain.create("您？"), quote=source
                        )
                if (
                    skip_review.result
                    and member.id in yaml_data["Basic"]["Permission"]["Admin"]
                ):
                    logger.info("跳过审核")
                else:
                    logger.info("开始审核")
                    moderation = await text_moderation_async(text)
                    if moderation["status"] == "error":
                        return await safeSendGroupMessage(
                            group,
                            MessageChain.create("漂流瓶内容审核失败，请稍后重新丢漂流瓶！"),
                            quote=source,
                        )
                    elif not moderation["status"]:
                        return await safeSendGroupMessage(
                            group,
                            MessageChain.create(
                                f"你的漂流瓶内可能包含违规内容{moderation['message']}，请检查后重新丢漂流瓶！"
                            ),
                            quote=source,
                        )
            elif len(text) > 400:
                return await safeSendGroupMessage(
                    group,
                    MessageChain.create("你的漂流瓶内容过长（400）！"),
                    quote=source,
                )

        if message_chain.has(Image):
            if arg_pic.matched or arg_reg_pic.matched:
                return await safeSendGroupMessage(
                    group, MessageChain.create("使用手动发图参数后不可附带图片"), quote=source
                )
            elif len(message_chain.get(Image)) > 1:
                return await safeSendGroupMessage(
                    group, MessageChain.create("丢漂流瓶只能携带一张图片哦！"), quote=source
                )
            else:
                image_url = message_chain.getFirst(Image).url

    if arg_pic.matched or arg_reg_pic.matched:
        await safeSendGroupMessage(
            group, MessageChain.create("请在 30 秒内发送你要附带的图片"), quote=source
        )
        try:
            image_url = await asyncio.wait_for(inc.wait(image_waiter), 30)
            if image_url:
                await safeSendGroupMessage(
                    group, MessageChain.create("图片已接收，请稍等"), quote=source
                )
            else:
                return await safeSendGroupMessage(
                    group, MessageChain.create("你发送的不是“一张”图片，请重试"), quote=source
                )
        except asyncio.TimeoutError:
            return await safeSendGroupMessage(
                group, MessageChain.create("图片等待超时"), quote=source
            )

    if image_url:
        if skip_review.result and member.id in yaml_data["Basic"]["Permission"]["Admin"]:
            logger.info("跳过审核")
        else:
            logger.info("开始审核")
            moderation = await image_moderation_async(image_url)
            if not moderation["status"]:
                return await safeSendGroupMessage(
                    group,
                    MessageChain.create(
                        f"你的漂流瓶包含违规内容 {moderation['message']}，请检查后重新丢漂流瓶！"
                    ),
                )
            elif moderation["status"] == "error":
                return await safeSendGroupMessage(
                    group, MessageChain.create("图片审核失败，请稍后重试！")
                )
        async with httpx.AsyncClient() as client:
            resp = await client.get(image_url)
            image_type = resp.headers["Content-Type"]
            image = resp.content
            image_name = str(time.time()) + "." + image_type.split("/")[1]
            IMAGE_PATH.joinpath(image_name).write_bytes(image)
            if image:

                if (
                    skip_review.result
                    and member.id in yaml_data["Basic"]["Permission"]["Admin"]
                ):
                    logger.info("跳过审核")
                else:
                    if qrdecode(image):
                        if member.id in user_list["black"]:
                            pass
                        else:
                            user_list["black"].append(member.id)
                            save_config()
                        return await safeSendGroupMessage(
                            group, MessageChain.create("漂流瓶不能携带二维码哦！你已被拉黑")
                        )
            else:
                return await safeSendGroupMessage(
                    group, MessageChain.create("图片异常，请稍后重试！")
                )

    if text or image_name:
        if await reduce_gold(member.id, 8):
            bottle = throw_bottle(member, text, image_name)
            in_bottle_text = "一段文字" if text else ""
            in_bottle_image = "一张图片" if image_name else ""
            in_bottle_and = "和" if in_bottle_text and in_bottle_image else ""
            in_bottle = in_bottle_text + in_bottle_and + in_bottle_image
            await safeSendGroupMessage(
                group,
                MessageChain.create(
                    [
                        At(member.id),
                        Plain(f" 成功购买漂流瓶并丢出！\n瓶子里有{in_bottle}\n瓶子编号为：{bottle}"),
                    ]
                ),
                quote=source,
            )
        else:
            await safeSendGroupMessage(
                group, MessageChain.create(f"你的{COIN_NAME}不足，无法丢漂流瓶！"), quote=source
            )
    else:
        return await safeSendGroupMessage(
            group, MessageChain.create("丢漂流瓶请加上漂流瓶的内容！"), quote=source
        )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch(r"^(捡|打?捞)(漂流瓶|瓶子)|lplp|gdb$")])],
        decorators=[
            Function.require("DriftingBottle"),
            Permission.require(),
            # RollQQ.require(),
            Interval.require(30),
        ],
    )
)
async def pick_bottle_handler(group: Group, member: Member):
    bottle = get_bottle()

    if bottle is None:
        return await safeSendGroupMessage(group, MessageChain.create("没有漂流瓶可以捡哦！"))
    if not await reduce_gold(member.id, 2):
        return await safeSendGroupMessage(
            group, MessageChain.create(f"你的{COIN_NAME}不足，无法捞漂流瓶！")
        )
    bottle_score = get_bottle_score_avg(bottle["id"])
    bottle_discuss = get_bottle_discuss(bottle["id"])
    score_msg = f"瓶子的评分为：{bottle_score}" if bottle_score else "本漂流瓶目前还没有评分"
    discuss_msg = (
        f"\n这个瓶子当前有 {len(bottle_discuss)} 条评论\n" if bottle_discuss else "\n本漂流瓶目前还没有评论"
    )

    times = bottle["fishing_times"]
    times_msg = f"本漂流瓶已经被捞了{str(times)}次" if times > 0 else "本漂流瓶还没有被捞到过"
    msg = [
        At(member),
        f" 你捡到了一个漂流瓶！\n瓶子编号为：{bottle['id']}\n{times_msg}\n{score_msg}\n" "漂流瓶内容为：\n",
    ]
    if bottle["text"] is not None:
        image = await create_image(bottle["text"])
        msg.append(Image(data_bytes=image))
    if bottle["image"] is not None:
        if bottle["text"]:
            msg.append("\n")
        msg.append(Image(path=IMAGE_PATH.joinpath(bottle["image"])))
    msg.append(discuss_msg)
    if bottle_discuss:
        discuss_img = [
            f"{i} 楼. {discuss.discuss_time} | {discuss.member}：\n      > {discuss.discuss}"
            for i, discuss in enumerate(bottle_discuss, start=1)
        ]

        discuss_img = await create_image("\n".join(discuss_img))
        msg.append(Image(data_bytes=discuss_img))
    await safeSendGroupMessage(group, MessageChain.create(msg))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("清空漂流瓶")])],
        decorators=[Permission.require(Permission.MASTER), Interval.require()],
    )
)
async def clear_bottle_handler(group: Group):

    clear_bottle()
    await safeSendGroupMessage(group, MessageChain.create("漂流瓶已经清空！"))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([FullMatch("查漂流瓶"), "bottleid" @ WildcardMatch(optional=True)])
        ],
        decorators=[
            Function.require("DriftingBottle"),
            Permission.require(),
            Interval.require(),
        ],
    )
)
async def drifting_bottle_handler(group: Group, member: Member, bottleid: RegexResult):
    if bottleid.matched:
        if bottleid.result.asDisplay().isdigit():
            bottle_id = int(bottleid.result.asDisplay())
        else:
            return await safeSendGroupMessage(group, MessageChain.create("漂流瓶编号必须是数字！"))
        bottle = get_bottle_by_id(bottle_id)

        if not bottle:
            return await safeSendGroupMessage(group, MessageChain.create("没有这个漂流瓶！"))

        bottle = bottle[0]
        if (
            member.id == yaml_data["Basic"]["Permission"]["Master"]
            or bottle.member == member.id
        ):
            bottle_score = get_bottle_score_avg(bottle_id)
            bottle_discuss = get_bottle_discuss(bottle_id)
            score_msg = f"瓶子的评分为：{bottle_score}" if bottle_score else "本漂流瓶目前还没有评分"
            discuss_msg = (
                f"\n这个瓶子当前有 {len(bottle_discuss)} 条评论\n"
                if bottle_discuss
                else "\n本漂流瓶目前还没有评论"
            )

            msg = [
                Plain(
                    f"漂流瓶编号为：{bottle.id}\n"
                    f"丢出时间为：{bottle.send_date}\n"
                    f"漂流瓶来自 {bottle.group} 群的 {bottle.member}\n{score_msg}\n"
                )
            ]
            if bottle.text is not None:
                image = await create_image(bottle.text)
                msg.append(Image(data_bytes=image))
            if bottle.image is not None:
                if bottle.text:
                    msg.append("\n")
                msg.append(Image(path=IMAGE_PATH.joinpath(bottle.image)))
            msg.append(discuss_msg)
            if bottle_discuss:
                discuss_img = [
                    f"{i} 楼. {discuss.discuss_time} | {discuss.member}：\n      > {discuss.discuss}"
                    for i, discuss in enumerate(bottle_discuss, start=1)
                ]
                discuss_img = await create_image("\n".join(discuss_img))
                msg.append(Image(data_bytes=discuss_img))
            await safeSendGroupMessage(group, MessageChain.create(msg))
        else:
            await safeSendGroupMessage(group, MessageChain.create("你没有权限查看这个漂流瓶！"))
    else:
        count = count_bottle()
        my_bottles = get_my_bottles(member)
        msg = [
            f"目前有 {count} 个漂流瓶在漂流" if count > 0 else "目前没有漂流瓶在漂流",
            "\n漂流瓶可以使用“捞漂流瓶”命令捞到，也可以使用“丢漂流瓶”命令丢出”\n可以使用“漂流瓶评分”为漂流瓶添加评分",
        ]
        if my_bottles:
            msg.append(f"\n截至目前你共丢出 {len(my_bottles)} 个漂流瓶：\n")
            my_bottles_str = "\n".join(
                [f"编号：{x}，日期{x.send_date}，群号：{x.group}" for x in my_bottles]
            )
            msg.append(Image(data_bytes=await create_image(my_bottles_str)))
        else:
            msg.append("\n截至目前你还没有丢出过漂流瓶")
        await safeSendGroupMessage(
            group,
            MessageChain.create(msg),
        )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([FullMatch("删漂流瓶"), "anything" @ WildcardMatch(optional=True)])
        ],
        decorators=[Permission.require(), Interval.require()],
    )
)
async def delete_bottle_handler(group: Group, member: Member, anything: RegexResult):

    if anything.matched:
        if anything.result.asDisplay().isdigit():
            bottle_id = int(anything.result.asDisplay())
            bottle = get_bottle_by_id(bottle_id)
            if not bottle:
                return await safeSendGroupMessage(group, MessageChain.create("没有这个漂流瓶！"))
            bottle = bottle[0]
            if (
                member.id == yaml_data["Basic"]["Permission"]["Master"]
                or bottle.member == member.id
            ):
                delete_bottle(bottle_id)
                await safeSendGroupMessage(group, MessageChain.create("漂流瓶已经删除！"))
            else:
                await safeSendGroupMessage(group, MessageChain.create("你没有权限删除这个漂流瓶！"))
        else:
            await safeSendGroupMessage(group, MessageChain.create("漂流瓶编号必须是数字！"))
    else:
        await safeSendGroupMessage(group, MessageChain.create("请输入要删除的漂流瓶编号！"))


def qrdecode(img):
    image = IMG.open(BytesIO(img))
    image_array = np.array(image)
    image_data = pyzbar.decode(image_array)
    return len(image_data)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    ElementMatch(At, optional=True),
                    FullMatch("漂流瓶评分"),
                    "anythings" @ WildcardMatch(optional=True),
                ]
            )
        ],
        decorators=[
            Function.require("DriftingBottle"),
            Permission.require(),
            Interval.require(5),
        ],
    )
)
async def bottle_score_handler(
    group: Group, member: Member, message: MessageChain, anythings: RegexResult
):
    if anythings.matched:
        try:
            saying = anythings.result.asDisplay().split(" ", 2)
            if message.has(Quote):
                reply = message.getFirst(Quote)
                if reply.senderId != yaml_data["Basic"]["MAH"]["BotQQ"]:
                    return await safeSendGroupMessage(
                        group, MessageChain.create(At(member.id), " 请正确回复漂流瓶，并输入分数")
                    )
                if not (
                    reg_search := re.search(r"瓶子编号为：(.*)\n", reply.origin.asDisplay())
                ):
                    return await safeSendGroupMessage(
                        group, MessageChain.create(At(member.id), " 请正确回复漂流瓶，并输入分数")
                    )
                bottle_id = reg_search[1]
                score = anythings.result.asDisplay()
            else:
                bottle_id = saying[0]
                score = saying[1]

            if bottle_id.isdigit() and score.isdigit():
                score = int(score)
                if get_bottle_by_id(bottle_id):
                    if 1 <= score <= 5:
                        if add_bottle_score(bottle_id, member, score):
                            bottle_score = get_bottle_score_avg(bottle_id)
                            await safeSendGroupMessage(
                                group,
                                MessageChain.create(
                                    At(member.id), f" 漂流瓶评分成功，当前评分{bottle_score}"
                                ),
                            )
                        else:
                            await safeSendGroupMessage(
                                group,
                                MessageChain.create(At(member.id), " 你已对该漂流瓶评过分，请勿重复评分"),
                            )
                    else:
                        await safeSendGroupMessage(
                            group, MessageChain.create(At(member.id), " 评分仅可为1-5分")
                        )
                else:
                    await safeSendGroupMessage(
                        group, MessageChain.create(At(member.id), " 没有这个漂流瓶")
                    )

            else:
                await safeSendGroupMessage(
                    group, MessageChain.create(At(member.id), " 请输入正确的漂流瓶编号和分数！")
                )
        except Exception:
            await safeSendGroupMessage(
                group, MessageChain.create(At(member.id), " 使用方式：漂流瓶评分 <漂流瓶编号> <分数>")
            )
    else:
        await safeSendGroupMessage(
            group, MessageChain.create(At(member.id), " 使用方式：漂流瓶评分 <漂流瓶编号> <分数>")
        )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    ElementMatch(At, optional=True),
                    FullMatch("漂流瓶评论"),
                    "anythings" @ WildcardMatch(optional=True),
                ]
            )
        ],
        decorators=[
            Function.require("DriftingBottle"),
            Permission.require(),
            Interval.require(5),
        ],
    )
)
async def bottle_discuss_handler(
    group: Group,
    member: Member,
    message: MessageChain,
    anythings: RegexResult,
    source: Source,
):
    if anythings.matched:
        try:
            if anythings.result.has(Image):
                return await safeSendGroupMessage(
                    group, MessageChain.create(At(member.id), " 不支持图片评论！")
                )

            saying = anythings.result.asDisplay().split(" ", 2)
            if message.has(Quote):
                reply = message.getFirst(Quote)
                if reply.senderId != yaml_data["Basic"]["MAH"]["BotQQ"]:
                    return await safeSendGroupMessage(
                        group, MessageChain.create(At(member.id), " 请正确回复漂流瓶，并输入评论内容")
                    )
                if not (
                    reg_search := re.search(r"瓶子编号为：(.*)\n", reply.origin.asDisplay())
                ):
                    return await safeSendGroupMessage(
                        group,
                        MessageChain.create(At(member.id), " 请正确回复漂流瓶，并输入评论内容"),
                    )
                bottle_id = reg_search[1]
                discuss = anythings.result.asDisplay()
            else:
                bottle_id = saying[0]
                discuss = saying[1]

            if bottle_id.isdigit():
                if get_bottle_by_id(bottle_id):
                    if 3 <= len(discuss) <= 500:
                        moderation = await text_moderation_async(discuss)
                        if moderation["status"] == "error":
                            return await safeSendGroupMessage(
                                group,
                                MessageChain.create("评论内容审核失败，请稍后重新评论！"),
                                quote=source,
                            )
                        elif not moderation["status"]:
                            return await safeSendGroupMessage(
                                group,
                                MessageChain.create(
                                    f"你的评论内可能包含违规内容{moderation['message']}，请检查后重新评论！"
                                ),
                                quote=source,
                            )
                        if add_bottle_discuss(bottle_id, member, discuss):
                            bottle_discuss = get_bottle_discuss(bottle_id)
                            await safeSendGroupMessage(
                                group,
                                MessageChain.create(
                                    At(member.id),
                                    f" 漂流瓶评论成功，当前共有 {len(bottle_discuss)} 条评论",
                                ),
                            )
                        else:
                            await safeSendGroupMessage(
                                group,
                                MessageChain.create(
                                    At(member.id), " 你已对该漂流瓶发表过 3 条评论，无法再次发送"
                                ),
                            )
                    else:
                        await safeSendGroupMessage(
                            group,
                            MessageChain.create(At(member.id), " 评论字数需在 3-500 字之间"),
                        )
                else:
                    await safeSendGroupMessage(
                        group, MessageChain.create(At(member.id), " 没有这个漂流瓶")
                    )
            else:
                await safeSendGroupMessage(
                    group, MessageChain.create(At(member.id), " 请输入正确的漂流瓶编号！")
                )
        except Exception:
            await safeSendGroupMessage(
                group, MessageChain.create(At(member.id), " 使用方式：漂流瓶评论 <漂流瓶编号> <评论内容>")
            )
    else:
        await safeSendGroupMessage(
            group, MessageChain.create(At(member.id), " 使用方式：漂流瓶评论 <漂流瓶编号> <评论内容>")
        )
