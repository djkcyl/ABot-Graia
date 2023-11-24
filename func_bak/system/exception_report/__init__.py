import traceback

from io import StringIO
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.element import Image
from graia.broadcast.builtin.event import ExceptionThrowed
from graia.saya.builtins.broadcast.schema import ListenerSchema

from core_bak.model import FuncType
from core_bak.config import ABotConfig
from util.text2image import md2img
from core_bak.function import build_metadata


channel = Channel.current()
channel.meta = build_metadata(
    func_type=FuncType.system,
    name="异常事件汇报",
    version="1.0",
    description="收到未捕获的异常时，将会向主人汇报",
    can_be_disabled=False,
    hidden=True,
)


@channel.use(ListenerSchema(listening_events=[ExceptionThrowed]))
async def except_handle(event: ExceptionThrowed):
    app = Ariadne.current()
    if not isinstance(event.event, ExceptionThrowed):
        with StringIO() as fp:
            traceback.print_tb(event.exception.__traceback__, file=fp)
            tb = fp.getvalue()
        msg = str(
            f"# 异常事件：\n\n> {str(event.event)}"
            + f"\n\n# 异常追踪：\n\n```{tb}\n{type(event.exception)}: {str(event.exception)}```"
        )
        await app.send_friend_message(
            ABotConfig.master,
            ["发生未捕获的异常\n", Image(data_bytes=await md2img(msg, 1400))],
        )
