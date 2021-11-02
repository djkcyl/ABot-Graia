from loguru import logger
from graia.saya import Saya, Channel
from graia.ariadne.model import Group
from graia.ariadne.app import Ariadne
from graia.ariadne.message.element import Image
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.scheduler.timers import every_custom_minutes
from graia.scheduler.saya.schema import SchedulerSchema
from graia.ariadne.event.lifecycle import ApplicationLaunched
from graia.ariadne.message.parser.literature import Literature
from graia.saya.builtins.broadcast.schema import ListenerSchema

from database.db import get_ranking
from util.text2image import create_image
from util.limit import member_limit_check
from util.UserBlock import group_black_list_block

saya = Saya.current()
channel = Channel.current()

RANK_LIST = None


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Literature("查看排行榜")],
                            decorators=[member_limit_check(5), group_black_list_block()]))
async def main(app: Ariadne, group: Group):
    await app.sendGroupMessage(group, MessageChain.create([Image(data_bytes=RANK_LIST)]))


@channel.use(SchedulerSchema(every_custom_minutes(10)))
async def something_scheduled(app: Ariadne):
    global RANK_LIST
    msg = await get_ranking()
    RANK_LIST = await create_image(msg, 100)
    logger.info("排行榜已生成完毕")


@channel.use(ListenerSchema(listening_events=[ApplicationLaunched]))
async def bot_Launched(app: Ariadne):

    global RANK_LIST
    msg = await get_ranking()
    RANK_LIST = await create_image(msg, 100)
    logger.info("排行榜已生成完毕")
