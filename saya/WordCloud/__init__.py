import re
import time
import numpy
import asyncio
import jieba.analyse

from io import BytesIO
from pathlib import Path

from PIL import Image as IMG
from matplotlib import pyplot
from graia.saya import Channel
from graia.ariadne.model import Group, Member
from wordcloud import ImageColorGenerator, WordCloud
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At, Image, Plain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import RegexMatch, Twilight

from util.sendMessage import safeSendGroupMessage
from util.control import Function, Interval, Permission
from database.usertalk import get_group_talk, get_user_talk

channel = Channel.current()

BASEPATH = Path(__file__).parent
MASK = numpy.array(IMG.open(BASEPATH.joinpath("bgg.jpg")))
FONT_PATH = Path("font").joinpath("sarasa-mono-sc-regular.ttf")
STOPWORDS = BASEPATH.joinpath("stopwords")

RUNNING = 0
RUNNING_LIST = []


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([RegexMatch(r"^查看(个人|本群)词云")])],
        decorators=[
            Function.require("WordCloud"),
            Permission.require(),
            Interval.require(150),
        ],
    )
)
async def wordcloud(group: Group, member: Member, message: MessageChain):

    global RUNNING, RUNNING_LIST
    pattern = re.compile(r"^查看(个人|本群)词云")
    if match := pattern.match(message.asDisplay()):
        if RUNNING < 5:
            RUNNING += 1
            RUNNING_LIST.append(member.id)
            mode = match[1]
            before_week = int(time.time() - 604800)
            if mode == "个人":
                talk_list = await get_user_talk(
                    str(member.id), str(group.id), before_week
                )
            elif mode == "本群":
                talk_list = await get_group_talk(str(group.id), before_week)
            if len(talk_list) < 10:
                await safeSendGroupMessage(
                    group, MessageChain.create([Plain("当前样本量较少，无法制作")])
                )
                RUNNING -= 1
                return RUNNING_LIST.remove(member.id)
            await safeSendGroupMessage(
                group,
                MessageChain.create(
                    [At(member.id), Plain(f" 正在制作词云，一周内共 {len(talk_list)} 条记录")]
                ),
            )
            words = await get_frequencies(talk_list)
            image = await asyncio.to_thread(make_wordcloud, words)
            await safeSendGroupMessage(
                group,
                MessageChain.create(
                    [At(member.id), Plain(f" 已成功制作{mode}词云"), Image(data_bytes=image)]
                ),
            )
            RUNNING -= 1
            RUNNING_LIST.remove(member.id)
        else:
            await safeSendGroupMessage(
                group, MessageChain.create([Plain("词云生成进程正忙，请稍后")])
            )


async def get_frequencies(msg_list):
    text = "\n".join(msg_list)
    words = jieba.analyse.extract_tags(text, topK=800, withWeight=True)
    return dict(words)


def make_wordcloud(words):

    wordcloud = WordCloud(
        font_path=str(FONT_PATH),
        background_color="white",
        mask=MASK,
        max_words=800,
        scale=2,
    )
    wordcloud.generate_from_frequencies(words)
    image_colors = ImageColorGenerator(MASK, default_color=(255, 255, 255))
    wordcloud.recolor(color_func=image_colors)
    pyplot.imshow(wordcloud.recolor(color_func=image_colors), interpolation="bilinear")
    pyplot.axis("off")
    image = wordcloud.to_image()
    imageio = BytesIO()
    image.save(imageio, format="JPEG", quality=98)
    return imageio.getvalue()
