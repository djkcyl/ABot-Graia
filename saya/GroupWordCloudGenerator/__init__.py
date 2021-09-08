import re
import pkuseg
import numpy as np
import matplotlib.pyplot as plt

from PIL import Image as IMG
from datetime import datetime
from graia.saya import Saya, Channel
from dateutil.relativedelta import relativedelta
from graia.application.group import Group, Member
from graia.application import GraiaMiraiApplication
from wordcloud import WordCloud, ImageColorGenerator
from graia.application.exceptions import AccountMuted
from graia.application.event.messages import GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.elements.internal import At, MessageChain, Plain, Image

from config import yaml_data, group_data
from util.RestControl import rest_control
from util.limit import member_limit_check
from util.UserBlock import black_list_block

from .Sqlite3Manager import execute_sql


saya = Saya.current()
channel = Channel.current()
seg = pkuseg.pkuseg()

BASE_PATH = "./saya/GroupWordCloudGenerator/"
GWCGRAINING = False


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            headless_decorators=[rest_control(), black_list_block()]))
async def group_wordcloud_generator(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):

    if yaml_data['Saya']['WordCloud']['Disabled']:
        return
    elif 'WordCloud' in group_data[group.id]['DisabledFunc']:
        return

    message_text = message.asDisplay()
    member_id = member.id
    group_id = group.id
    if1 = "[图片]" not in message_text
    if2 = "[表情]" not in message_text
    ifat = not message.has(At)
    if if1 & if2 & ifat:
        await write_chat_record(seg, group_id, member_id, message_text)
    try:
        global GWCGRAINING
        if message_text == "我的月内总结":
            if GWCGRAINING:
                await app.sendGroupMessage(group, MessageChain.create([Plain("有一个其他的总结正在运行中，请稍后再试")]))
                return
            GWCGRAINING = True
            await app.sendGroupMessage(group, MessageChain.create([Plain("正在生成，请稍后")]))
            await app.sendGroupMessage(group, await get_review(group_id, member_id, "month", "member"))
            GWCGRAINING = False
        elif message_text == "我的年内总结":
            if GWCGRAINING:
                await app.sendGroupMessage(group, MessageChain.create([Plain("有一个其他的总结正在运行中，请稍后再试")]))
                return
            GWCGRAINING = True
            await app.sendGroupMessage(group, MessageChain.create([Plain("正在生成，请稍后")]))
            await app.sendGroupMessage(group, await get_review(group_id, member_id, "year", "member"))
            GWCGRAINING = False
        elif message_text == "本群月内总结":
            if GWCGRAINING:
                await app.sendGroupMessage(group, MessageChain.create([Plain("有一个其他的总结正在运行中，请稍后再试")]))
                return
            GWCGRAINING = True
            await app.sendGroupMessage(group, MessageChain.create([Plain("正在生成，请稍后")]))
            await app.sendGroupMessage(group, await get_review(group_id, member_id, "month", "group"))
            GWCGRAINING = False
        elif message_text == "本群年内总结":
            if GWCGRAINING:
                await app.sendGroupMessage(group, MessageChain.create([Plain("有一个其他的总结正在运行中，请稍后再试")]))
                return
            GWCGRAINING = True
            await app.sendGroupMessage(group, MessageChain.create([Plain("正在生成，请稍后")]))
            await app.sendGroupMessage(group, await get_review(group_id, member_id, "year", "group"))
            GWCGRAINING = False
    except AccountMuted:
        pass


async def count_words(sp, n):
    w = {}
    for i in sp:
        if i not in w:
            w[i] = 1
        else:
            w[i] += 1
    top = sorted(w.items(), key=lambda item: (-item[1], item[0]))
    top_n = top[:n]
    return top_n


async def filter_label(label_list: list) -> list:
    """
    Filter labels

    Args:
        label_list: Words to filter

    Examples:
        result = await filter_label(label_list)

    Return:
        list
    """
    not_filter = ["草"]
    image_filter = "mirai:"
    result = []
    for i in label_list:
        if image_filter in i:
            continue
        elif i in not_filter:
            result.append(i)
        elif len(i) != 1 and i.find('nbsp') < 0:
            result.append(i)
    return result


async def write_chat_record(seg, group_id: int, member_id: int, content: str) -> None:
    content = content.replace("\\", "/")
    filter_words = re.findall(r"\[mirai:(.*?)\]", content, re.S)
    for i in filter_words:
        content = content.replace(f"[mirai:{i}]", "")
    content = content.replace("\"", " ")
    seg_result = seg.cut(content)
    seg_result = await filter_label(seg_result)
    # print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    sql = f"""INSERT INTO chatRecord 
                (`time`, groupId, memberId, content, seg)
                VALUES
                (\"{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\", {group_id}, {member_id}, \"{content}\",
                \"{','.join(seg_result)}\") """
    await execute_sql(sql)


async def draw_word_cloud(read_name):
    mask = np.array(IMG.open(f'{BASE_PATH}bgg.jpg'))
    # print(mask.shape)
    wc = WordCloud(
        font_path=f'{BASE_PATH}STKAITI.TTF',
        background_color='white',
        # max_words=500,
        max_font_size=180,
        width=1890,
        height=1417,
        mask=mask
    )
    name = []
    value = []
    for t in read_name:
        name.append(t[0])
        value.append(t[1])
    for i in range(len(name)):
        name[i] = str(name[i])
        # name[i] = name[i].encode('gb2312').decode('gb2312')
    dic = dict(zip(name, value))
    # print(dic)
    # print(len(dic.keys()))
    wc.generate_from_frequencies(dic)
    image_colors = ImageColorGenerator(mask, default_color=(255, 255, 255))
    # print(image_colors.image.shape)
    wc.recolor(color_func=image_colors)
    plt.imshow(wc.recolor(color_func=image_colors), interpolation="bilinear")
    # plt.imshow(wc)
    plt.axis("off")
    # plt.show()
    wc.to_file(f'{BASE_PATH}tempWordCloud.png')


async def get_review(group_id: int, member_id: int, review_type: str, target: str) -> MessageChain:
    time = datetime.now()
    year, month, day, hour, minute, second = time.strftime(
        "%Y %m %d %H %M %S").split(" ")
    if review_type == "year":
        yearp, monthp, dayp, hourp, minutep, secondp = (
            time - relativedelta(years=1)).strftime("%Y %m %d %H %M %S").split(" ")
        tag = "年内"
    elif review_type == "month":
        yearp, monthp, dayp, hourp, minutep, secondp = (
            time - relativedelta(months=1)).strftime("%Y %m %d %H %M %S").split(" ")
        tag = "月内"
    else:
        return MessageChain.create([
            Plain(text="Error: review_type invalid!")
        ])

    sql = f"""SELECT * FROM chatRecord 
                    WHERE 
                groupId={group_id} {f'AND memberId={member_id}' if target == 'member' else ''} 
                AND time<'{year}-{month}-{day} {hour}:{minute}:{second}'
                AND time>'{yearp}-{monthp}-{dayp} {hourp}:{minutep}:{secondp}'"""
    # print(sql)
    res = await execute_sql(sql)
    texts = []
    for i in res:
        if i[4]:
            texts += i[4].split(",")
        else:
            texts.append(i[3])
    # print(texts)
    top_n = await count_words(texts, 20000)
    await draw_word_cloud(top_n)
    sql = f"""SELECT count(*) FROM chatRecord 
                    WHERE 
                groupId={group_id} {f'AND memberId={member_id}' if target == 'member' else ''}  
                AND time<'{year}-{month}-{day} {hour}:{minute}:{second}'
                AND time>'{yearp}-{monthp}-{dayp} {hourp}:{minutep}:{secondp}'"""
    res = await execute_sql(sql)
    times = res[0][0]
    return MessageChain.create([
        At(member_id),
        Plain(
            text=f"\n自有记录以来，{'你' if target == 'member' else '本群'}一共发了{times}条消息\n下面是{'你的' if target == 'member' else '本群的'}{tag}词云:\n"),
        Image.fromLocalFile(f"{BASE_PATH}tempWordCloud.png")
    ])
