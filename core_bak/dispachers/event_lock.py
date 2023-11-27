from graia.ariadne.event.mirai import MiraiEvent
from graia.ariadne.event.lifecycle import ApplicationLaunched
from graia.broadcast.entities.dispatcher import BaseDispatcher
from graia.broadcast.interfaces.dispatcher import DispatcherInterface

from core_bak.event_lock import event_lock


class EventLockDispatcher(BaseDispatcher):
    @staticmethod
    async def beforeExecution(interface: DispatcherInterface[MiraiEvent]):
        if isinstance(interface.event, ApplicationLaunched) or event_lock.is_set():
            return
        interface.stop()

    @staticmethod
    async def catch(interface: DispatcherInterface[MiraiEvent]):
        pass
