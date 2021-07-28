from graia.application import GraiaMiraiApplication
from graia.application.exceptions import AccountMuted, UnknownTarget
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.event.messages import *
from graia.application.event.mirai import *
from graia.application.message.elements.internal import *

from config import yaml_data, group_data


saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupRecallEvent]))
async def anitRecall(app: GraiaMiraiApplication, events: GroupRecallEvent):

    if yaml_data['Saya']['AnitRecall']['Disabled']:
        return
    elif 'AnitRecall' in group_data[events.group.id]['DisabledFunc']:
        return

    if events.authorId != yaml_data["Basic"]["MAH"]["BotQQ"]:
        try:
            print(f"防撤回触发：[{events.group.name}({str(events.group.id)})]")
            recallEvents = await app.messageFromId(events.messageId)
            recallMsg = recallEvents.messageChain
            authorMember = await app.getMember(events.group.id, events.authorId)
            authorName = "自己" if events.operator.id == events.authorId else authorMember.name
            msg = MessageChain.join(
                MessageChain.create([
                    Plain(f"{events.operator.name}({events.operator.id})撤回了{authorName}的一条消息:"),
                    Plain(f"\n=====================\n")]),
                recallMsg)
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
