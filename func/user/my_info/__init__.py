from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.element import Image, Source
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import Twilight, FullMatch

from util.text2image import md2img
from core.preprocessor import MentionMe
from core.function import build_metadata
from core.model import AUserModel, FuncType
from core.control import Function, Permission, Interval

channel = Channel.current()
channel.meta = build_metadata(
    func_type=FuncType.user,
    name="个人信息",
    version="1.0",
    description="查看个人信息，例如签到天数等",
    usage=["发送指令：查看个人信息"],
)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([FullMatch("查看个人信息")], preprocessor=MentionMe()),
        ],
        decorators=[Function.require(), Permission.require(), Interval.require()],
    )
)
async def main(app: Ariadne, group: Group, source: Source, auser: AUserModel):
    await app.send_group_message(
        group,
        Image(
            data_bytes=await md2img(
                f"# 个人信息\n\n"
                f"- 签到天数：{auser.total_sign}\n"
                f"- 签到连续天数：{auser.continue_sign}\n"
                f"- 游戏币：{auser.coin}\n"
                f"- 从有记录以来共 {auser.totle_talk} 次发言\n"
            )
        ),
        quote=source,
    )
