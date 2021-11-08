from loguru import logger
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.mirai import GroupRecallEvent
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.exception import AccountMuted, UnknownTarget
from graia.ariadne.message.element import Plain, Image, FlashImage, Xml, Json, Voice

from config import yaml_data, group_data
from util.TextModeration import text_moderation
from util.ImageModeration import image_moderation
from util.sendMessage import safeSendGroupMessage


saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupRecallEvent]))
async def anitRecall(app: Ariadne, events: GroupRecallEvent):

    if events.authorId != yaml_data["Basic"]["MAH"]["BotQQ"] or events.operator.id == yaml_data["Basic"]["MAH"]["BotQQ"]:
        try:
            logger.info(f"防撤回触发：[{events.group.name}({str(events.group.id)})]")
            recallMsg = await app.getMessageFromId(events.messageId)
            authorMember = await app.getMember(events.group.id, events.authorId)
            authorName = "自己" if events.operator.id == events.authorId else authorMember.name
            msg = MessageChain.join(
                MessageChain.create([
                    Plain(f"{events.operator.name}({events.operator.id})撤回了{authorName}的一条消息:"),
                    Plain("\n=====================\n")
                ]),
                recallMsg)

            if recallMsg.has(Image):
                for image in recallMsg.get(Image):
                    res = await image_moderation(image.url)
                    if res['Suggestion'] != "Pass":
                        if 'AnitRecall' not in group_data[str(events.group.id)]['DisabledFunc'] and not yaml_data['Saya']['AnitRecall']['Disabled']:
                            try:
                                await app.mute(events.group, events.authorId, 60)
                            except Exception:
                                pass
                            await safeSendGroupMessage(events.group, MessageChain.create([
                                Plain(f"{events.operator.name}({events.operator.id})撤回了{authorName}的一条消息:"),
                                Plain("\n=====================\n"),
                                Plain(f"（由于撤回图片内包含 {res['Label']} / {res['SubLabel']} 违规，不予防撤回）")
                            ]))
                            return
            if recallMsg.has(Plain):
                for text in recallMsg.get(Plain):
                    res = await text_moderation(text.text)
                    if res['Suggestion'] != "Pass":
                        if 'AnitRecall' not in group_data[str(events.group.id)]['DisabledFunc'] and not yaml_data['Saya']['AnitRecall']['Disabled']:
                            try:
                                await app.mute(events.group, events.authorId, 60)
                            except Exception:
                                pass
                            await safeSendGroupMessage(events.group, MessageChain.create([
                                Plain(f"{events.operator.name}({events.operator.id})撤回了{authorName}的一条消息:"),
                                Plain("\n=====================\n"),
                                Plain(f"\n（由于撤回文字内包含 {res['Label']} 违规，不予防撤回）")
                            ]))
                            return
            if 'AnitRecall' not in group_data[str(events.group.id)]['DisabledFunc'] and not yaml_data['Saya']['AnitRecall']['Disabled']:
                if recallMsg.has(Voice) or recallMsg.has(Xml) or recallMsg.has(Json):
                    pass
                elif recallMsg.has(FlashImage):
                    await safeSendGroupMessage(events.group, MessageChain.create([
                        Plain("闪照不予防撤回")
                    ]))
                else:
                    await safeSendGroupMessage(events.group, msg.asSendable())
        except (AccountMuted, UnknownTarget):
            pass
