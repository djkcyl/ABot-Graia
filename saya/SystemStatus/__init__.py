import psutil
import asyncio
import platform

from pathlib import Path
from graia.saya import Saya, Channel
from graia.application.group import Group
from graia.application import GraiaMiraiApplication
from graia.scheduler.timers import every_custom_seconds
from graia.scheduler.saya.schema import SchedulerSchema
from graia.application.event.messages import GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.event.lifecycle import ApplicationLaunched
from graia.application.message.parser.literature import Literature
from graia.application.message.elements.internal import Image_UnsafeBytes, MessageChain

from util.limit import member_limit_check
from util.UserBlock import group_black_list_block

from .mapping import get_mapping

CPU_USAGE = [0] * 300
MEM_USAGE = [0] * 300
saya = Saya.current()
channel = Channel.current()
psutil.cpu_percent()


@channel.use(SchedulerSchema(every_custom_seconds(1)))
async def update_scheduled():
    global CPU_USAGE, MEM_USAGE

    if len(CPU_USAGE) == 300:
        CPU_USAGE = CPU_USAGE[-299:]
    CPU_USAGE.append(psutil.cpu_percent())
    if len(MEM_USAGE) == 300:
        MEM_USAGE = MEM_USAGE[-299:]
    MEM_USAGE.append(int(psutil.virtual_memory().used / 1000000))


@channel.use(ListenerSchema(listening_events=[ApplicationLaunched]))
async def cpuStatus(app: GraiaMiraiApplication):
    await asyncio.sleep(0.1)
    virtual_memory = psutil.virtual_memory()
    disk = psutil.disk_usage(Path.cwd())
    app.logger.info("=========================")
    app.logger.info(f"当前系统：{platform.system()}")
    app.logger.info(f"CPU核心数：{psutil.cpu_count()}")
    app.logger.info(f"内存：{int(virtual_memory.used / 1000000)}MB / {int(virtual_memory.total / 1000000)}MB")
    app.logger.info(f"硬盘：{int(disk.used / 1000000)}MB / {int(disk.total / 1000000)}MB")
    app.logger.info("已开始记录 CPU 占用率")
    app.logger.info("已开始记录内存占用率")
    app.logger.info("=========================")


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Literature("查看性能统计")],
                            headless_decorators=[member_limit_check(15), group_black_list_block()]))
async def get_image(app: GraiaMiraiApplication, group: Group):
    image = await get_mapping(CPU_USAGE, MEM_USAGE, int(psutil.virtual_memory().total / 1000000))
    await app.sendGroupMessage(group, MessageChain.create([Image_UnsafeBytes(image.getvalue())]))
