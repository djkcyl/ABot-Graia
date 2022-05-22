from loguru import logger
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.mirai import GroupRecallEvent
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.element import (
    App,
    Xml,
    Json,
    Voice,
    Plain,
    Image,
    FlashImage,
)

from config import yaml_data, group_data
from util.sendMessage import safeSendGroupMessage
from util.TextModeration import text_moderation_async
from util.ImageModeration import image_moderation_async

channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupRecallEvent]))
async def anitRecall(app: Ariadne, events: GroupRecallEvent):
    if (
        "AnitRecall" in group_data[str(events.group.id)]["DisabledFunc"]
        or yaml_data["Saya"]["AnitRecall"]["Disabled"]
    ):
        return
    if (
        events.authorId != yaml_data["Basic"]["MAH"]["BotQQ"]
        or events.operator.id == yaml_data["Basic"]["MAH"]["BotQQ"]
    ):
        logger.info(f"防撤回触发：[{events.group.name}({str(events.group.id)})]")
        recallMsg = await app.getMessageFromId(events.messageId)
        authorMember = await app.getMember(events.group.id, events.authorId)
        authorName = "自己" if events.operator.id == events.authorId else authorMember.name
        msg = MessageChain.create(
            [
                Plain(
                    f"{events.operator.name}({events.operator.id})撤回了{authorName}的一条消息:"
                ),
                Plain("\n=====================\n"),
            ]
        ).extend(recallMsg.messageChain)

        if recallMsg.messageChain.has(Image):
            for image in recallMsg.messageChain.get(Image):
                res = await image_moderation_async(image.url)
                if not res["status"]:
                    await safeSendGroupMessage(
                        events.group,
                        MessageChain.create(
                            [
                                Plain(
                                    f"{events.operator.name}({events.operator.id})撤回了{authorName}的一条消息:"
                                ),
                                Plain("\n=====================\n"),
                                Plain(f"（由于撤回图片内包含 {res['message']} 违规，不予防撤回）"),
                            ]
                        ),
                    )
                    return
        if recallMsg.messageChain.has(Plain):
            for text in recallMsg.messageChain.get(Plain):
                res = await text_moderation_async(text.text)
                if not res["status"]:
                    await safeSendGroupMessage(
                        events.group,
                        MessageChain.create(
                            [
                                Plain(
                                    f"{events.operator.name}({events.operator.id})撤回了{authorName}的一条消息:"
                                ),
                                Plain("\n=====================\n"),
                                Plain(f"\n（由于撤回文字内包含 {res['message']} 违规，不予防撤回）"),
                            ]
                        ),
                    )
                    return

        if (
            recallMsg.messageChain.has(Voice)
            or recallMsg.messageChain.has(Xml)
            or recallMsg.messageChain.has(Json)
            or recallMsg.messageChain.has(App)
        ):
            pass
        elif recallMsg.messageChain.has(FlashImage):
            await safeSendGroupMessage(
                events.group, MessageChain.create([Plain("闪照不予防撤回")])
            )
        else:
            await safeSendGroupMessage(events.group, msg.asSendable())
