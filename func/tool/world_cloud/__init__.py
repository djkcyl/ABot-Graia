from io import BytesIO
from typing import Annotated
from graia.saya import Channel
from wordcloud import WordCloud
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group, Member
from graia.ariadne.message.element import Image
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import Twilight, FullMatch, UnionMatch, ResultValue

from util import get_message
from core.model import FuncType
from core.preprocessor import MentionMe
from core.function import build_metadata
from core.model import TimeRange, DataSource
from core.control import Function, Permission, Interval

channel = Channel.current()
channel.meta = build_metadata(
    func_type=FuncType.tool,
    name="词云",
    version="1.0",
    description="生成词云",
    usage=["发送指令：词云 [自己/本群/全局] [周/月/年]"],
    options=[
        {"name": "source", "help": "数据来源，必选：自己/本群/全局"},
        {"name": "time", "help": "时间范围，必选：周/月/年"},
    ],
    example=[
        {"run": "词云", "to": "查看本周群词云"},
        {"run": "词云 自己 年", "to": "查看本年自己的词云"},
    ],
)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    FullMatch("词云"),
                    "arg_source" @ UnionMatch("自己", "本群", "全局"),
                    "arg_time" @ UnionMatch("周", "月", "年"),
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
):  # sourcery skip: comprehension-to-generator
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
    query = await get_message(
        source, member.id if source == DataSource.SELF else group.id, time_range, False
    )
    message_list = [message for _, message in query]

    message_count = sum([await i.count() for i in message_list])
    if message_count < 100:
        return await app.send_group_message(group, "已记录的消息数量过少，无法生成词云")

    message_text = []
    for message in message_list:
        for i in await message.to_list():
            message_text.append(i.message_tokenizer)

    message_text = [
        i.message_tokenizer or "" for message in message_list for i in await message.to_list()
    ]
    message_text = " ".join(message_text)

    wordcloud = WordCloud(
        font_path="static/font/HarmonyOS_Sans_SC_Medium.ttf",
        background_color="white",
        width=800,
        height=600,
        max_words=400,
        max_font_size=100,
        min_font_size=10,
    )
    wordcloud.generate(message_text)

    image = wordcloud.to_image()
    image_bytes = BytesIO()
    image.save(image_bytes, format="jpeg", quality=95, optimize=True)

    await app.send_group_message(group, Image(data_bytes=image_bytes.getvalue()))
