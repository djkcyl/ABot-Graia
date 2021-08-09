import re
import json
import requests

from PIL import Image, ImageDraw, ImageFont

from graia.saya import Saya, Channel
from graia.application.group import Group, Member
from graia.application import GraiaMiraiApplication
from graia.application.event.messages import GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.elements.internal import MessageChain, At, Plain, Image_UnsafeBytes


from util.aiorequests import aiorequests
from config import save_config, yaml_data, group_data, group_list

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def bilibili_main(app: GraiaMiraiApplication, group: Group, message: MessageChain):

    # 如果为卡片消息
    if group.id == 790380594:
        p = re.compile('av(\d{1,12})|BV(1[A-Za-z0-9]{2}4.1.7[A-Za-z0-9]{2})')
        video_number = p.search(message.to_string())
        if video_number:
            video_number = video_number.group(0)
            if video_number:
                print(video_number)
                if video_number[:2] == "av":
                    video_info = requests.get(f"http://api.bilibili.com/x/web-interface/view?aid={video_number[2:]}")

                    print("av")
                elif video_number[:2] == "BV":
                    video_number = bv_to_av(video_number)
                    video_info = requests.get(f"http://api.bilibili.com/x/web-interface/view?aid={video_number}")


def bv_to_av(bv: str) -> int:
    table = 'fZodR9XQDSUm21yCkr6zBqiveYah8bt4xsWpHnJE7jL5VG3guMTKNPAwcF'
    tr = {}
    for i in range(58):
        tr[table[i]] = i
    s = [11, 10, 3, 8, 4, 6]
    xor = 177451812
    add = 8728348608
    r = 0
    for i in range(6):
        r += tr[bv[s[i]]] * 58 ** i
    return (r - add) ^ xor


async def draw_video_info(video_info):
    
    # 处理动态信息
    dynamic = video_info['data']['dynamic']





def getCutStr(str, cut):
    si = 0
    i = 0
    next_str = str
    str_list = []
    for s in next_str:
        if '\u4e00' <= s <= '\u9fff':
            si += 1.5
        else:
            si += 1
        i += 1
        if si > cut:
            str_list.append(next_str[:i])
            next_str = next_str[i:]
        else:
            next_str = [str]

    return next_str

print(getCutStr("图像库为Python解释器添加了图像处理功能。. 此库提供了广泛的文件格式支持、高效的内部表示和相当强大的图像处理功能。", 14))