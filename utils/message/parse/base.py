"""移植自 Ariadne"""

import abc

from graia.amnesia.message.chain import MessageChain
from graia.broadcast.builtin.derive import Derive
from graia.broadcast.entities.decorator import Decorator
from graia.broadcast.interfaces.decorator import DecoratorInterface
from graia.broadcast.interfaces.dispatcher import DispatcherInterface


class ChainDecorator(abc.ABC, Decorator, Derive[MessageChain]):
    pre = True

    @abc.abstractmethod
    async def __call__(self, chain: MessageChain, interface: DispatcherInterface) -> MessageChain | None:
        ...

    async def target(self, interface: DecoratorInterface):
        return await self(
            await interface.dispatcher_interface.lookup_param("message_chain", MessageChain, None),
            interface.dispatcher_interface,
        )
