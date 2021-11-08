import re
import httpx
import asyncio

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group, Member
from graia.broadcast.exceptions import ExecutionStop
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Plain
from graia.saya.builtins.broadcast.schema import ListenerSchema

from config import yaml_data, group_data
from util.control import Permission, Interval
from util.sendMessage import safeSendGroupMessage

from .draw_bili_image import binfo_image_create

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage], decorators=[Permission.require()]))
async def bilibili_main(app: Ariadne, group: Group, member: Member, message: MessageChain):

    if yaml_data['Saya']['BilibiliResolve']['Disabled']:
        return
    elif 'BilibiliResolve' in group_data[str(group.id)]['DisabledFunc']:
        return

    saying = message.asPersistentString()
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
            await Interval.manual(member.id)
            return await safeSendGroupMessage(group, MessageChain.create([Plain("视频不存在")]))
        else:
            await Interval.manual(int(video_info["data"]["aid"]))
        try:
            image = await asyncio.to_thread(binfo_image_create, video_info)
            await safeSendGroupMessage(group, MessageChain.create([Image(data_bytes=image)]))
        except Exception as err:
            await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
                Plain(f"B站视频 {video_number} 解析失败\n{err}")
            ]))
            await safeSendGroupMessage(group, MessageChain.create([Plain("API 调用频繁，请10分钟后重试")]))


async def b23_extract(text):
    b23 = re.compile(r'b23.tv\\/(\w+)').search(text)
    if not b23:
        b23 = re.compile(r'b23.tv/(\w+)').search(text)
    try:
        url = f'https://b23.tv/{b23[1]}'
    except TypeError:
        raise ExecutionStop()
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, follow_redirects=True)
    r = str(resp.url)
    return r


async def video_info_get(id):
    async with httpx.AsyncClient() as client:
        if id[:2] == "av":
            video_info = await client.get(f"http://api.bilibili.com/x/web-interface/view?aid={id[2:]}")
            video_info = video_info.json()
        elif id[:2] == "BV":
            video_info = await client.get(f"http://api.bilibili.com/x/web-interface/view?bvid={id}")
            video_info = video_info.json()
        return video_info
