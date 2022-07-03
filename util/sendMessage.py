from typing import Optional, Union, Iterable

from graia.ariadne import get_running
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.model import BotMessage, Group, Member, Friend
from graia.ariadne.message.element import At, Plain, Source, Element
from graia.ariadne.exception import UnknownTarget, RemoteException, AccountMuted

from config import yaml_data


async def safeSendGroupMessage(
    target: Union[Group, int],
    message: Union[MessageChain, Iterable[Element], Element, str],
    quote: Optional[Union[Source, int]] = None,
) -> BotMessage:
    app = get_running(Ariadne)
    if not isinstance(message, MessageChain):
        message = MessageChain.create(message)
    try:
        return await app.sendGroupMessage(target, message, quote=quote)
    except UnknownTarget:
        msg = []
        for element in message.__root__:
            if isinstance(element, At):
                member = await app.getMember(target, element.target)
                name = member.name if member else str(element.target)
                msg.append(Plain(name))
                continue
            msg.append(element)
        return await app.sendGroupMessage(target, MessageChain.create(msg), quote=quote)

    except AccountMuted:
        group_id = target.id if isinstance(target, Group) else target
        await app.sendFriendMessage(
            yaml_data["Basic"]["Permission"]["Master"],
            MessageChain.create(f"由于 Bot 在 {group_id} 群被封禁，正在退出"),
        )
        await app.quitGroup(target)

    except RemoteException as e:
        if "LIMITED" in str(e):
            group_id = target.id if isinstance(target, Group) else target
            await app.sendFriendMessage(
                yaml_data["Basic"]["Permission"]["Master"],
                MessageChain.create(f"由于 {group_id} 群开启消息限制，正在退出"),
            )
            await app.quitGroup(target)
        elif "被禁言" in str(e):
            group_id = target.id if isinstance(target, Group) else target
            await app.sendFriendMessage(
                yaml_data["Basic"]["Permission"]["Master"],
                MessageChain.create(f"由于 Bot 在 {group_id} 群被封禁，正在退出"),
            )

            await app.quitGroup(target)


async def autoSendMessage(
    target: Union[Member, Friend, str],
    message: Union[MessageChain, Iterable[Element], Element, str],
    quote: Optional[Union[Source, int]] = None,
) -> BotMessage:
    """根据输入的目标类型自动选取发送好友信息或是群组信息"""
    app = get_running(Ariadne)
    if isinstance(target, str):
        target = int(target)
    if not isinstance(message, MessageChain):
        message = MessageChain.create(message)
    if isinstance(target, Member):
        return await app.sendGroupMessage(target, message, quote=quote)
    elif isinstance(target, (Friend, int)):
        return await app.sendFriendMessage(target, message, quote=quote)
