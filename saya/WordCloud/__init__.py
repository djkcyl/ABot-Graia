import re
import numpy
import asyncio
import jieba.analyse

from PIL import Image
from io import BytesIO
from matplotlib import pyplot
from graia.saya import Saya, Channel
from graia.application.group import Group, Member
from concurrent.futures import ThreadPoolExecutor
from graia.application import GraiaMiraiApplication
from wordcloud import WordCloud, ImageColorGenerator
from graia.application.event.messages import GroupMessage
from graia.application.message.parser.kanata import Kanata
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.parser.signature import RegexMatch
from graia.application.message.elements.internal import MessageChain, At, Plain, Image_UnsafeBytes

from util.limit import member_limit_check
from util.UserBlock import group_black_list_block
from config import yaml_data, group_data, sendmsg
from datebase.usertalk import get_user_talk, get_group_talk, add_talk

saya = Saya.current()
channel = Channel.current()
loop = asyncio.get_running_loop()
pool = ThreadPoolExecutor()

BAST_PATH = "./saya/WordCloud"
MASK_FILE = f'{BAST_PATH}/bgg.jpg'
FONT_PATH = './font/sarasa-mono-sc-regular.ttf'


RUNNING = 0
RUNNING_LIST = []


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Kanata([RegexMatch("查看(个人|本群)词云")])],
                            headless_decorators=[member_limit_check(300), group_black_list_block()]))
async def wordcloud(app: GraiaMiraiApplication, group: Group, member: Member, message: MessageChain):

    global RUNNING, RUNNING_LIST
    pattern = re.compile("^查看(个人|本群)词云")
    match = pattern.match(message.asDisplay())

    if match:

        if yaml_data['Saya']['WordCloud']['Disabled']:
            return await sendmsg(app=app, group=group)
        elif 'WordCloud' in group_data[group.id]['DisabledFunc']:
            return await sendmsg(app=app, group=group)

        if RUNNING < 5:
            RUNNING += 1
            RUNNING_LIST.append(member.id)
            mode = match.group(1)
            if mode == "个人":
                talk_list = await get_user_talk(str(member.id), str(group.id))
            elif mode == "本群":
                talk_list = await get_group_talk(str(group.id))
            if len(talk_list) < 10:
                await app.sendGroupMessage(group, MessageChain.create([
                    Plain("当前样本量较少，无法制作")
                ]))
                RUNNING -= 1
                return RUNNING_LIST.remove(member.id)
            app.logger.info(f"正在制作词云，共 {len(talk_list)} 条记录")
            await app.sendGroupMessage(group, MessageChain.create([
                At(member.id),
                Plain(f" 正在制作词云，共 {len(talk_list)} 条记录")
            ]))
            words = await get_frequencies(talk_list)
            image = await loop.run_in_executor(pool, make_wordcloud, words)
            await app.sendGroupMessage(group, MessageChain.create([
                At(member.id),
                Plain(f" 已成功制作{mode}词云"),
                Image_UnsafeBytes(image)
            ]))
            RUNNING -= 1
            RUNNING_LIST.remove(member.id)
        else:
            await app.sendGroupMessage(group, MessageChain.create([
                Plain("词云生成进程正忙，请稍后")
            ]))


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            headless_decorators=[group_black_list_block()]))
async def add_talk_word(group: Group, member: Member, message: MessageChain):
    if message.has(Plain):
        plain_list = message.get(Plain)
        plain = MessageChain.create(plain_list).asDisplay()
        await add_talk(str(member.id), str(group.id), plain)


async def get_frequencies(msg_list):
    text = "\n".join(msg_list)
    words = jieba.analyse.extract_tags(text, topK=800, withWeight=True)
    return dict(words)


def make_wordcloud(words):
    image = Image.open(MASK_FILE)
    mask = numpy.array(image)
    wordcloud = WordCloud(
        font_path=FONT_PATH,
        background_color='white',
        mask=mask,
        max_words=800,
        scale=2
    )
    wordcloud.generate_from_frequencies(words)
    image_colors = ImageColorGenerator(mask, default_color=(255, 255, 255))
    wordcloud.recolor(color_func=image_colors)
    pyplot.imshow(wordcloud.recolor(color_func=image_colors), interpolation="bilinear")
    pyplot.axis("off")
    image = wordcloud.to_image()
    imageio = BytesIO()
    image.save(imageio, format="JPEG", quality=98)
    return imageio.getvalue()
