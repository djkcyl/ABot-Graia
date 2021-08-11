import re
import asyncio

from graia.saya import Saya, Channel
from graia.application.group import Group
from concurrent.futures import ThreadPoolExecutor
from graia.application import GraiaMiraiApplication
from graia.application.event.messages import GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.elements.internal import MessageChain, Image_UnsafeBytes, Plain

from util.limit import manual_limit
from util.aiorequests import aiorequests
from config import yaml_data, group_data

from .draw_bili_image import binfo_image_create

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def bilibili_main(app: GraiaMiraiApplication, group: Group, message: MessageChain):

    if yaml_data['Saya']['BilibiliResolve']['Disabled']:
        return
    elif 'BilibiliResolve' in group_data[group.id]['DisabledFunc']:
        return

    saying = message.to_string()
    video_info = None
    if "b23.tv" in saying:
        saying = await b23_extract(saying)
    p = re.compile(r'av(\d{1,12})|BV(1[A-Za-z0-9]{2}4.1.7[A-Za-z0-9]{2})')
    video_number = p.search(saying)
    if video_number:
        video_number = video_number.group(0)
        if video_number:
            video_info = await video_info_get(video_number)
    if video_info:
        if video_info["code"] != 0:
            manual_limit(group.id, "BilibiliResolve", 5)
            return await app.sendGroupMessage(group, MessageChain.create([Plain("视频不存在")]))
        print(video_info)
        loop = asyncio.get_event_loop()
        pool = ThreadPoolExecutor(6)
        try:
            image = await loop.run_in_executor(pool, binfo_image_create, video_info)
            manual_limit(group.id, "BilibiliResolve", 20)
        except:
            await app.sendGroupMessage(group, MessageChain.create([Plain("API 调用频繁，请10分钟后重试")]))
            manual_limit(group.id, "BilibiliResolve", 600)
        else:
            await app.sendGroupMessage(group, MessageChain.create([Image_UnsafeBytes(image.getvalue())]))


async def b23_extract(text):
    b23 = re.compile(r'b23.tv\\/(\w+)').search(text)
    if not b23:
        b23 = re.compile(r'b23.tv/(\w+)').search(text)
    url = f'https://b23.tv/{b23[1]}'
    resp = await aiorequests.get(url)
    r = str(resp.url)
    print
    return r


async def video_info_get(id):
    if id[:2] == "av":
        video_info = await aiorequests.get(f"http://api.bilibili.com/x/web-interface/view?aid={id[2:]}")
        video_info = await video_info.json()
    elif id[:2] == "BV":
        video_info = await aiorequests.get(f"http://api.bilibili.com/x/web-interface/view?bvid={id}")
        video_info = await video_info.json()
    return video_info