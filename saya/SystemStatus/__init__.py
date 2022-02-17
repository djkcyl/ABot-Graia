import psutil
import asyncio
import platform

from pathlib import Path
from loguru import logger
from graia.saya import Saya, Channel
from graia.ariadne.model import Group
from graia.ariadne.message.element import Image
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.scheduler.timers import every_custom_seconds
from graia.scheduler.saya.schema import SchedulerSchema
from graia.ariadne.event.lifecycle import ApplicationLaunched
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import Twilight, FullMatch

from util.control import Permission
from util.sendMessage import safeSendGroupMessage

from .mapping import get_mapping

CPU_USAGE = [0] * 600
MEM_USAGE = [0] * 600
saya = Saya.current()
channel = Channel.current()
psutil.cpu_percent()


@channel.use(SchedulerSchema(every_custom_seconds(1)))
async def update_scheduled():
    global CPU_USAGE, MEM_USAGE

    if len(CPU_USAGE) == 600:
        CPU_USAGE = CPU_USAGE[-599:]
    CPU_USAGE.append(psutil.cpu_percent())
    if len(MEM_USAGE) == 600:
        MEM_USAGE = MEM_USAGE[-599:]
    MEM_USAGE.append(int(psutil.virtual_memory().used / 1048576))


@channel.use(ListenerSchema(listening_events=[ApplicationLaunched]))
async def cpuStatus():
    await asyncio.sleep(0.1)
    virtual_memory = psutil.virtual_memory()
    disk = psutil.disk_usage(str(Path.cwd()))
    logger.info("=========================")
    logger.info(f"当前系统：{platform.system()}")
    logger.info(f"CPU核心数：{psutil.cpu_count()}")
    logger.info(
        f"内存：{int(virtual_memory.used / 1048576)}MB / {int(virtual_memory.total / 1048576)}MB"
    )
    logger.info(f"硬盘：{int(disk.used / 1048576)}MB / {int(disk.total / 1048576)}MB")
    logger.info("已开始记录 CPU 占用率")
    logger.info("已开始记录内存占用率")
    logger.info("=========================")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight({"head": FullMatch("查看性能统计")})],
        decorators=[Permission.require(Permission.MASTER)],
    )
)
async def get_image(group: Group):
    image = await get_mapping(
        CPU_USAGE, MEM_USAGE, int(psutil.virtual_memory().total / 1000000)
    )
    await safeSendGroupMessage(group, MessageChain.create([Image(data_bytes=image)]))
