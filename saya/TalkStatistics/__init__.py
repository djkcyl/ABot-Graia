

from graia.saya import Saya, Channel
from graia.application.group import Group, Member
from graia.application import GraiaMiraiApplication
from graia.application.event.messages import GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.parser.literature import Literature
from graia.application.message.elements.internal import Image_UnsafeBytes, MessageChain

from util.limit import member_limit_check
from util.UserBlock import group_black_list_block
from datebase.usertalk import get_message_analysis

from .mapping import get_mapping

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Literature("查看消息量统计")],
                            headless_decorators=[member_limit_check(15), group_black_list_block()]))
async def get_image(app: GraiaMiraiApplication, group: Group):

    talk_num, time = await get_message_analysis()
    talk_num.reverse()
    time.reverse()
    image = await get_mapping(talk_num, time)

    await app.sendGroupMessage(group, MessageChain.create([Image_UnsafeBytes(image.getvalue())]))
