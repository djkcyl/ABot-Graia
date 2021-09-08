from graia.saya import Saya, Channel
from graia.application.group import Group
from graia.application import GraiaMiraiApplication
from graia.scheduler.timers import every_custom_minutes
from graia.scheduler.saya.schema import SchedulerSchema
from graia.application.event.messages import GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.event.lifecycle import ApplicationLaunched
from graia.application.message.parser.literature import Literature
from graia.application.message.elements.internal import Image_UnsafeBytes, MessageChain

from datebase.db import get_ranking
from util.text2image import create_image
from util.limit import member_limit_check
from util.UserBlock import black_list_block

saya = Saya.current()
channel = Channel.current()

RANK_LIST = None


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Literature("查看排行榜")],
                            headless_decorators=[member_limit_check(5), black_list_block()]))
async def main(app: GraiaMiraiApplication, group: Group):
    await app.sendGroupMessage(group, MessageChain.create([Image_UnsafeBytes(RANK_LIST.getvalue())]))


@channel.use(SchedulerSchema(every_custom_minutes(10)))
async def something_scheduled(app: GraiaMiraiApplication):
    global RANK_LIST
    msg = await get_ranking()
    RANK_LIST = await create_image(msg, 100)
    app.logger.info("排行榜已生成完毕")


@channel.use(ListenerSchema(listening_events=[ApplicationLaunched]))
async def something_scheduled(app: GraiaMiraiApplication):

    global RANK_LIST
    msg = await get_ranking()
    RANK_LIST = await create_image(msg, 100)
    app.logger.info("排行榜已生成完毕")
