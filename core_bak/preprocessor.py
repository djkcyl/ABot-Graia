from typing import Union, Optional
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.element import Element, Plain, At
from graia.ariadne.message.parser.base import ChainDecorator
from graia.broadcast.interfaces.dispatcher import DispatcherInterface


class MentionMe(ChainDecorator):
    """At 账号或者提到账号群昵称，如果有则提取，没有则不提取"""

    def __init__(self, name: Union[bool, str] = True) -> None:
        """
        Args:
            name (Union[bool, str]): 是否提取昵称, 如果为 True, 则自动提取昵称, \
            如果为 False 则禁用昵称, 为 str 则将参数作为昵称
        """
        self.name = name

    async def __call__(
        self, chain: MessageChain, interface: DispatcherInterface
    ) -> MessageChain:
        ariadne = Ariadne.current()
        name: Optional[str] = self.name if isinstance(self.name, str) else None
        if self.name is True:
            if isinstance(interface.event, GroupMessage):
                name = (
                    await ariadne.get_member(interface.event.sender.group, ariadne.account)
                ).name
            else:
                name = (await ariadne.get_bot_profile()).nickname
        first: Element = chain[0]
        if isinstance(name, str) and isinstance(first, Plain) and str(first).startswith(name):
            return chain.removeprefix(name).removeprefix(" ")
        if isinstance(first, At) and first.target == ariadne.account:
            return MessageChain(chain.__root__[1:], inline=True).removeprefix(" ")
        return chain
