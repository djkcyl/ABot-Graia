import traceback

from io import StringIO
from graia.saya import Saya, Channel
from graia.application import GraiaMiraiApplication
from graia.broadcast.builtin.event import ExceptionThrowed
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.elements.internal import Image_UnsafeBytes, MessageChain, Plain

from util.text2image import create_image
from config import yaml_data

saya = Saya.current()
channel = Channel.current()


async def make_msg_for_unknow_exception(event):
    with StringIO() as fp:
        traceback.print_tb(event.exception.__traceback__, file=fp)
        tb = fp.getvalue()
    msg = str(f"异常事件：\n{str(event.event)}" +
              f"\n异常类型：\n{str(type(event.exception))}" +
              f"\n异常内容：\n{event.exception.__str__()}" +
              f"\n异常追踪：\n{tb}")
    image = await create_image(msg, 200)
    return MessageChain.create([
        Plain("发生未捕获的异常\n"),
        Image_UnsafeBytes(image.getvalue())])


@channel.use(ListenerSchema(listening_events=[ExceptionThrowed]))
async def except_handle(app: GraiaMiraiApplication, event: ExceptionThrowed):
    if isinstance(event.event, ExceptionThrowed):
        return
    else:
        return await app.sendFriendMessage(
            yaml_data['Basic']['Permission']['Master'],
            await make_msg_for_unknow_exception(event)
        )
