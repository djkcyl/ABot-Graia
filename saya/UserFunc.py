from loguru import logger
from graia.saya import Channel
from graia.ariadne.model import Group, Member
from graia.ariadne.message.element import Image
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.scheduler.saya.schema import SchedulerSchema
from graia.scheduler.timers import every_custom_minutes
from graia.ariadne.event.lifecycle import ApplicationLaunched
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import FullMatch, Twilight

from config import COIN_NAME
from util.text2image import create_image
from database.db import get_info, get_ranking
from util.control import Interval, Permission
from util.sendMessage import safeSendGroupMessage

channel = Channel.current()

RANK_LIST = None


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("查看排行榜")])],
        decorators=[Permission.require(), Interval.require()],
    )
)
async def main(group: Group):
    await safeSendGroupMessage(group, MessageChain.create(Image(data_bytes=RANK_LIST)))


@channel.use(SchedulerSchema(every_custom_minutes(10)))
async def something_scheduled():
    global RANK_LIST
    msg = await get_ranking()
    RANK_LIST = await create_image(msg, 100)
    logger.info("排行榜已生成完毕")


@channel.use(ListenerSchema(listening_events=[ApplicationLaunched]))
async def bot_Launched():

    global RANK_LIST
    msg = await get_ranking()
    RANK_LIST = await create_image(msg, 100)
    logger.info("排行榜已生成完毕")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("查看个人信息")])],
        decorators=[Permission.require(), Interval.require()],
    )
)
async def get_user_info(group: Group, member: Member):
    user_info = await get_info(member.id)
    await safeSendGroupMessage(
        group,
        MessageChain.create(
            f"UID：{user_info[0]}\n",
            f"你已累计签到 {user_info[2]} 天\n",
            f"你已连续签到 {user_info[5]} 天\n",
            f"当前共有 {user_info[3]} 个{COIN_NAME}\n",
            f"从有记录以来你共有 {user_info[4]} 次发言",
        ),
    )
