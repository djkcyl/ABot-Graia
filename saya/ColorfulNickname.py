import random
import asyncio

from graia.ariadne.event.lifecycle import ApplicationLaunched
from graia.saya.builtins.broadcast.schema import ListenerSchema

from loguru import logger
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import MemberInfo
from graia.scheduler.timers import every_custom_minutes
from graia.scheduler.saya.schema import SchedulerSchema

from config import yaml_data


saya = Saya.current()
channel = Channel.current()

color_code = [
    "<&ÿĀĀĀ>",
    "<&ÿÿ5@>",
    "<&ÿÿ]>",
    "<&ÿÒUÐ>",
    "<&ÿÇý>",
    "<&ÿ ÄW>",
    "<&ÿÿÏP>",
    "<%ĀĀ Ð>",
    "<%ĀĀ Ñ>",
    "<%ĀĀ Ò>",
    "<%ĀĀ Ó>",
    "<%ĀĀ Ô>",
    "<%ĀĀ Õ>",
    "<%ĀĀ Ö>",
    "<%ĀĀ ×>",
    "<%ĀĀ Ø>",
    "<%ĀĀ Ù>",
    "<%ĀĀ Ú>",
    "<%ĀĀ Û>",
    "<%ĀĀ Ü>",
    "<%ĀĀ Ý>",
    "<%ĀĀ Þ>",
]


def generate_color_code() -> str:
    if random.randint(0, 1) == 0:
        return f"<&ÿ{''.join([chr(random.randint(0, 255)) for _ in range(3)])}>"
    else:
        return random.choice(color_code)


@channel.use(SchedulerSchema(every_custom_minutes(10)))
@channel.use(ListenerSchema(listening_events=[ApplicationLaunched]))
async def tasks(app: Ariadne):

    # 本功能已废弃，请勿开启，后果自负

    return

    group_list = (
        [await app.getGroup(yaml_data["Basic"]["Permission"]["DebugGroup"])]
        if yaml_data["Basic"]["Permission"]["Debug"]
        else await app.getGroupList()
    )
    for group in group_list:
        await app.modifyMemberInfo(
            group=group.id,
            member=yaml_data["Basic"]["MAH"]["BotQQ"],
            info=MemberInfo(
                name=f"{generate_color_code()}{yaml_data['Basic']['BotName']}"
            ),
        )
        await asyncio.sleep(0.1)
    logger.info(f"已完成 {len(group_list)} 个群的炫彩群名片更新")
