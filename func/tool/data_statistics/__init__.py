from loguru import logger
from typing import Annotated
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group, Member
from graia.ariadne.message.element import Image
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import Twilight, FullMatch, UnionMatch, ResultValue

from util import get_message
from core.model import FuncType
from util.text2image import html_render
from core.preprocessor import MentionMe
from core.function import build_metadata
from core.model import TimeRange, DataSource
from core.control import Function, Permission, Interval


from .render import render_message_line_chart


channel = Channel.current()
channel.meta = build_metadata(
    func_type=FuncType.tool,
    name="数据统计",
    version="1.0",
    description="查看各类数据统计，例如群消息量等",
    usage=["发送指令：数据统计 [自己/本群/全局] [日/周/月/年] [消息量]"],
    options=[
        {"name": "source", "help": "数据来源，必选：自己/本群/全局"},
        {"name": "time", "help": "时间范围，必选：日/周/月/年"},
        {"name": "type", "help": "数据类型，必选：消息量"},
    ],
    example=[
        {"run": "数据统计", "to": "查看本日群消息量"},
        {"run": "数据统计 自己 年", "to": "查看本年自己的消息量"},
    ],
    can_be_disabled=False,
)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    FullMatch("数据统计"),
                    "arg_source" @ UnionMatch("自己", "本群", "全局", optional=True),
                    "arg_time" @ UnionMatch("日", "周", "月", "年", optional=True),
                    "arg_type" @ UnionMatch("消息量", optional=True),
                ],
                preprocessor=MentionMe(),
            )
        ],
        decorators=[
            Function.require(),
            Permission.require(),
            Interval.require(),
        ],
    )
)
async def main(
    app: Ariadne,
    group: Group,
    member: Member,
    arg_source: Annotated[MessageChain, ResultValue()],
    arg_time: Annotated[MessageChain, ResultValue()],
    arg_type: Annotated[MessageChain, ResultValue()],
):
    if arg_type.display == "消息量":
        source_display_map = {
            "自己": DataSource.SELF,
            "本群": DataSource.GROUP,
            "全局": DataSource.GLOBAL,
        }
        time_display_map = {
            "日": TimeRange.DAY,
            "周": TimeRange.WEEK,
            "月": TimeRange.MONTH,
            "年": TimeRange.YEAR,
        }

        source = source_display_map[arg_source.display]
        time_range = time_display_map[arg_time.display]

        message_analysis = [
            (time, await query.count())
            for time, query in await get_message(
                source,
                member.id if source == DataSource.SELF else group.id,
                time_range,
                format_time=True,
            )
        ]
        message_analysis.reverse()

        logger.info(f"[Func.data_statistics] {message_analysis}")
        sub_title = f"{arg_source.display} / {arg_time.display}"
        await app.send_group_message(
            group,
            Image(
                data_bytes=await html_render.render(
                    render_message_line_chart(message_analysis, sub_title)
                )
            ),
        )
