from loguru import logger
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.event.lifecycle import ApplicationLaunched
from graia.saya.builtins.broadcast.schema import ListenerSchema

from core_bak.model import FuncType
from core_bak.event_lock import event_lock
from core_bak.function import build_metadata
from core_bak.dispachers.user import ABotDispatcher
from core_bak.dispachers.event_lock import EventLockDispatcher

channel = Channel.current()
channel.meta = build_metadata(
    func_type=FuncType.system,
    name="事件锁",
    version="1.0",
    description="用于在插件初始化完成后解锁监听器",
    can_be_disabled=False,
    hidden=True,
)


@channel.use(ListenerSchema(listening_events=[ApplicationLaunched], priority=12))
async def main_set(app: Ariadne):
    event_lock.set()
    app.broadcast.prelude_dispatchers.append(ABotDispatcher)
    logger.success("[Task.event_lock] 插件初始化完成，解锁监听器")


@channel.use(ListenerSchema(listening_events=[ApplicationLaunched], priority=0))
async def main_wait(app: Ariadne):
    app.broadcast.prelude_dispatchers.append(EventLockDispatcher)
    logger.info("[Task.event_lock] 正在等待插件初始化...")
