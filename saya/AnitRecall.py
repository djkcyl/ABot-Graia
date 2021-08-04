import json

from graia.saya import Saya, Channel
from graia.application import GraiaMiraiApplication
from graia.application.event.mirai import GroupRecallEvent
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.exceptions import AccountMuted, UnknownTarget
from graia.application.message.elements.internal import MessageChain, Plain, Image, FlashImage, Xml, Json, Voice

from config import yaml_data, group_data
from util.ImageModeration import image_moderation
from util.TextModeration import text_moderation


saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupRecallEvent]))
async def anitRecall(app: GraiaMiraiApplication, events: GroupRecallEvent):

    if yaml_data['Saya']['AnitRecall']['Disabled']:
        return

    if events.authorId != yaml_data["Basic"]["MAH"]["BotQQ"] or events.operator.id == yaml_data["Basic"]["MAH"]["BotQQ"]:
        try:
            print(f"防撤回触发：[{events.group.name}({str(events.group.id)})]")
            recallEvents = await app.messageFromId(events.messageId)
            recallMsg = recallEvents.messageChain
            authorMember = await app.getMember(events.group.id, events.authorId)
            authorName = "自己" if events.operator.id == events.authorId else authorMember.name
            msg = MessageChain.join(
                MessageChain.create([
                    Plain(f"{events.operator.name}({events.operator.id})撤回了{authorName}的一条消息:"),
                    Plain(f"\n=====================\n")
                ]),
                recallMsg)

            if recallMsg.has(Image):
                for image in recallMsg.get(Image):
                    res = await image_moderation(image.url)
                    try:
                        if res['Suggestion'] != "Pass":
                            if 'AnitRecall' not in group_data[events.group.id]['DisabledFunc']:
                                await app.sendGroupMessage(events.group, MessageChain.create([
                                    Plain(f"{events.operator.name}({events.operator.id})撤回了{authorName}的一条消息:"),
                                    Plain(f"\n=====================\n"),
                                    Plain(f"（由于撤回图片内包含 {res['Label']} / {res['SubLabel']} 违规，不予防撤回）")
                                ]))
                                try:
                                    await app.mute(events.group, events.authorId, 3600)
                                except:
                                    pass
                            await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], msg.asSendable())
                            return
                    except:
                        t = f"防撤回出错，内容为\n{json.dumps(res, indent=2, ensure_ascii=False)}"
                        print(t)
                        return await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
                            Plain(t)
                        ]))
            if recallMsg.has(Plain):
                for text in recallMsg.get(Plain):
                    res = await text_moderation(text.text)
                    try:
                        if res['Suggestion'] != "Pass":
                            if 'AnitRecall' not in group_data[events.group.id]['DisabledFunc']:
                                await app.sendGroupMessage(events.group, MessageChain.create([
                                    Plain(f"{events.operator.name}({events.operator.id})撤回了{authorName}的一条消息:"),
                                    Plain(f"\n=====================\n"),
                                    Plain(f"\n（由于撤回文字内包含 {res['Label']} 违规，不予防撤回）")
                                ]))
                                try:
                                    await app.mute(events.group, events.authorId, 3600)
                                except:
                                    pass
                            return
                    except:
                        t = f"防撤回出错，内容为\n{json.dumps(res, indent=2, ensure_ascii=False)}"
                        print(t)
                        return await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
                            Plain(t)
                        ]))

            if 'AnitRecall' not in group_data[events.group.id]['DisabledFunc']:
                if recallMsg.has(Voice) or recallMsg.has(Xml) or recallMsg.has(Json):
                    pass
                elif recallMsg.has(FlashImage):
                    await app.sendGroupMessage(events.group, MessageChain.create([
                        Plain(f"闪照不予防撤回")
                    ]))
                else:
                    await app.sendGroupMessage(events.group, msg.asSendable())
        except (AccountMuted, UnknownTarget):
            pass
