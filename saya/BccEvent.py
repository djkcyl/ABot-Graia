import traceback

from io import StringIO
from graia.saya import Channel
from graia.ariadne import get_running
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Plain
from graia.broadcast.builtin.event import ExceptionThrowed
from graia.saya.builtins.broadcast.schema import ListenerSchema

from config import yaml_data
from util.text2image import create_image
from util.sendMessage import safeSendGroupMessage

channel = Channel.current()


async def make_msg_for_unknow_exception(event: ExceptionThrowed):
    with StringIO() as fp:
        traceback.print_tb(event.exception.__traceback__, file=fp)
        tb = fp.getvalue()
    msg = str(
        f"异常事件：\n{str(event.event)}"
        + f"\n \n异常类型：\n{type(event.exception)}"
        + f"\n \n异常内容：\n{str(event.exception)}"
        + f"\n \n异常追踪：\n{tb}\n{str(event.exception)}"
    )
    image = await create_image(msg, 200)
    return MessageChain.create([Plain("发生未捕获的异常\n"), Image(data_bytes=image)])


@channel.use(ListenerSchema(listening_events=[ExceptionThrowed]))
async def except_handle(event: ExceptionThrowed):
    app = get_running(Ariadne)
    if isinstance(event.event, ExceptionThrowed):
        return
    else:
        eimg = await make_msg_for_unknow_exception(event)
        # try:
        #     if isinstance(event.event, GroupMessage):
        #         e: GroupMessage = event.event
        #         await safeSendGroupMessage(e.sender.group.id, eimg)
        # except Exception:
        #     pass
        return await app.sendFriendMessage(
            yaml_data["Basic"]["Permission"]["Master"],
            eimg,
        )
