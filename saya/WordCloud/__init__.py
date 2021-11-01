import re
import time
import numpy
import asyncio
import jieba.analyse

from PIL import Image
from io import BytesIO
from pathlib import Path
from matplotlib import pyplot
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group, Member
from concurrent.futures import ThreadPoolExecutor
from wordcloud import WordCloud, ImageColorGenerator
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import At, Plain, Image
from graia.ariadne.message.parser.literature import Literature
from graia.saya.builtins.broadcast.schema import ListenerSchema

from config import yaml_data, group_data
from util.limit import member_limit_check
from util.UserBlock import group_black_list_block
from database.usertalk import get_user_talk, get_group_talk

saya = Saya.current()
channel = Channel.current()
loop = asyncio.get_event_loop()
pool = ThreadPoolExecutor(4)

BASEPATH = Path(__file__).parent
MASK = numpy.array(Image.open(BASEPATH.joinpath('bgg.jpg')))
FONT_PATH = Path("font").joinpath("sarasa-mono-sc-regular.ttf").__str__()
STOPWORDS = BASEPATH.joinpath('stopwords')

RUNNING = 0
RUNNING_LIST = []


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Literature("查看个人词云"), Literature("查看本群词云")],
                            headless_decorators=[member_limit_check(300), group_black_list_block()]))
async def wordcloud(app: Ariadne, group: Group, member: Member, message: MessageChain):

    global RUNNING, RUNNING_LIST
    pattern = re.compile("^查看(个人|本群)词云")
    match = pattern.match(message.asDisplay())

    if match:

        if yaml_data['Saya']['WordCloud']['Disabled']:
            return
        elif 'WordCloud' in group_data[group.id]['DisabledFunc']:
            return

        if RUNNING < 5:
            RUNNING += 1
            RUNNING_LIST.append(member.id)
            mode = match.group(1)
            before_week = int(time.time()- 604800)
            if mode == "个人":
                talk_list = await get_user_talk(str(member.id), str(group.id), before_week)
            elif mode == "本群":
                talk_list = await get_group_talk(str(group.id), before_week)
            if len(talk_list) < 10:
                await app.sendGroupMessage(group, MessageChain.create([
                    Plain("当前样本量较少，无法制作")
                ]))
                RUNNING -= 1
                return RUNNING_LIST.remove(member.id)
            app.logger.info(f"正在制作词云，一周内共 {len(talk_list)} 条记录")
            await app.sendGroupMessage(group, MessageChain.create([
                At(member.id),
                Plain(f" 正在制作词云，一周内共 {len(talk_list)} 条记录")
            ]))
            words = await get_frequencies(talk_list)
            image = await loop.run_in_executor(pool, make_wordcloud, words)
            await app.sendGroupMessage(group, MessageChain.create([
                At(member.id),
                Plain(f" 已成功制作{mode}词云"),
                Image(data_bytes=image)
            ]))
            RUNNING -= 1
            RUNNING_LIST.remove(member.id)
        else:
            await app.sendGroupMessage(group, MessageChain.create([
                Plain("词云生成进程正忙，请稍后")
            ]))


async def get_frequencies(msg_list):
    text = "\n".join(msg_list)
    words = jieba.analyse.extract_tags(text, topK=800, withWeight=True)
    return dict(words)


def make_wordcloud(words):
    
    wordcloud = WordCloud(
        font_path=FONT_PATH,
        background_color='white',
        mask=MASK,
        max_words=800,
        scale=2
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
