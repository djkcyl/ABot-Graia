import os
import json
import time
import asyncio
import requests

from pathlib import Path
from graiax import silkcoder
from graia.saya import Saya, Channel
from graia.application.friend import Friend
from graia.application.group import Group, Member
from graia.broadcast.interrupt.waiter import Waiter
from graia.application import GraiaMiraiApplication
from graia.broadcast.interrupt import InterruptControl
from graia.application.event.messages import FriendMessage, GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.parser.literature import Literature
from graia.application.message.elements.internal import Image_UnsafeBytes, MessageChain, Plain, Image_NetworkAddress, Voice, Source

from config import yaml_data, group_data, sendmsg
from datebase.db import reduce_gold
from util.aiorequests import aiorequests
from util.text2image import create_image
from util.limit import member_limit_check
from util.RestControl import rest_control


saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
inc = InterruptControl(bcc)

if not os.path.exists("./saya/CloudMusic/temp/"):
    print("正在创建音乐缓存文件夹")
    os.mkdir("./saya/CloudMusic/temp/")

MIRAI_PATH = "/A60/bot/"

if not os.path.exists(f"{MIRAI_PATH}data/net.mamoe.mirai-api-http/voices/"):
    print("请打开./saya/CloudMusic/__init__.py 并修改第 31 行的地址为Mirai的根目录")
    exit()


HOST = "http://127.0.0.1:3000"
if not yaml_data['Saya']['CloudMusic']['Disabled']:
    phone = yaml_data['Saya']['CloudMusic']['ApiConfig']['PhoneNumber']
    password = yaml_data['Saya']['CloudMusic']['ApiConfig']['Password']
    login = requests.get(f"{HOST}/login/cellphone?phone={phone}&password={password}").cookies

WAITING = []


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Literature("点歌")],
                            headless_decorators=[rest_control(), member_limit_check(300)]))
async def what_are_you_saying(app: GraiaMiraiApplication, group: Group, member: Member, message: MessageChain, source: Source):

    if yaml_data['Saya']['CloudMusic']['Disabled']:
        return await sendmsg(app=app, group=group)
    elif 'CloudMusic' in group_data[group.id]['DisabledFunc']:
        return await sendmsg(app=app, group=group)

    @Waiter.create_using_function([GroupMessage])
    async def waiter1(waiter1_group: Group, waiter1_member: Member, waiter1_message: MessageChain):
        if all([waiter1_group.id == group.id, waiter1_member.id == member.id]):
            waiter1_saying = waiter1_message.asDisplay()
            if waiter1_saying == "取消":
                return False
            else:
                return waiter1_saying

    @Waiter.create_using_function([GroupMessage])
    async def waiter2(waiter2_group: Group, waiter2_member: Member, waiter2_message: MessageChain):
        if all([waiter2_group.id == group.id, waiter2_member.id == member.id]):
            if waiter2_message.asDisplay() == "取消":
                return False
            elif waiter2_message.asDisplay() in ["1", "2", "3", "4", "5", "6", "7", "8", "8", "10"]:
                return waiter2_message.asDisplay()
            else:
                await app.sendGroupMessage(group, MessageChain.create([Plain("请发送歌曲 id<1-10> 来点歌，发送取消可终止本次点歌")]))

    if member.id not in WAITING:
        saying = message.asDisplay().split(" ", 1)
        WAITING.append(member.id)

        if len(saying) == 1:
            waite_musicmessageId = await app.sendGroupMessage(group, MessageChain.create([Plain(f"请发送歌曲名，发送取消即可终止点歌")]))
            try:
                musicname = await asyncio.wait_for(inc.wait(waiter1), timeout=15)
                if not musicname:
                    WAITING.remove(member.id)
                    return await app.sendGroupMessage(group, MessageChain.create([Plain("已取消点歌")]))
            except asyncio.TimeoutError:
                WAITING.remove(member.id)
                return await app.sendGroupMessage(group, MessageChain.create([
                    Plain("点歌超时")
                ]), quote=waite_musicmessageId.messageId)
        else:
            musicname = saying[1]
        times = str(int(time.time()))
        search = requests.get(
            url=f"{HOST}/cloudsearch?keywords={musicname}&timestamp={times}", cookies=login)
        if json.loads(search.text)["result"]["songCount"] == 0:
            WAITING.remove(member.id)
            return await app.sendGroupMessage(group, MessageChain.create([Plain("未找到此歌曲")]))
        musiclist = json.loads(search.text)["result"]["songs"]
        musicIdList = []
        msg = "为你在网易云音乐找到以下歌曲！\n==============================="
        num = 1
        for music in musiclist:
            if num > 10:
                break
            music_id = music['id']
            music_name = music['name']
            music_ar = []
            for ar in music['ar']:
                music_ar.append(ar['name'])
            music_ar = "/".join(music_ar)
            num_str = " " + str(num) if num < 10 else str(num)
            msg += f"\n{num_str}    ===>    {music_name} - {music_ar}"
            musicIdList.append(music_id)
            num += 1
        msg += f"\n===============================\n发送歌曲id可完成点歌\n发送取消可终止当前点歌\n点歌将消耗 4 个游戏币"
        image = await create_image(msg)
        waite_musicmessageId = await app.sendGroupMessage(group, MessageChain.create([
            Image_UnsafeBytes(image.getvalue())
        ]))

        try:
            wantMusicID = await asyncio.wait_for(inc.wait(waiter2), timeout=30)
            if not wantMusicID:
                WAITING.remove(member.id)
                return await app.sendGroupMessage(group, MessageChain.create([Plain("已取消点歌")]))
        except asyncio.TimeoutError:
            WAITING.remove(member.id)
            return await app.sendGroupMessage(group, MessageChain.create([
                Plain("点歌超时")
            ]), quote=waite_musicmessageId.messageId)

        musicid = musicIdList[int(wantMusicID) - 1]
        times = str(int(time.time()))
        musicinfo = requests.get(
            url=f"{HOST}/song/detail?ids={musicid}&timestamp={times}",
            cookies=login).json()
        # print(musicinfo)
        musicurl = requests.get(
            url=f"{HOST}/song/url?id={musicid}&br=128000&timestamp={times}",
            cookies=login).json()

        if not os.path.exists(f"./saya/CloudMusic/temp/{musicid}.mp3"):
            music_url = musicurl["data"][0]["url"]
            if music_url == None:
                WAITING.remove(member.id)
                return await app.sendGroupMessage(group, MessageChain.create([Plain("该歌曲暂无法点歌")]), quote=source)
            r = await aiorequests.get(music_url)
            music_fcontent = await r.content
            print(f"正在缓存歌曲：{music_name}")
            with open(f'./saya/CloudMusic/temp/{musicid}.mp3', 'wb') as f:
                f.write(music_fcontent)

        if not await reduce_gold(str(member.id), 4):
            WAITING.remove(member.id)
            return await app.sendGroupMessage(group, MessageChain.create([Plain("你的游戏币不足，无法使用")]), quote=source)

        if yaml_data['Saya']['CloudMusic']['MusicInfo']:
            music_name = musicinfo['songs'][0]['name']
            music_ar = []
            for ar in musicinfo['songs'][0]['ar']:
                music_ar.append(ar['name'])
            music_ar = "/".join(music_ar)
            music_al = musicinfo['songs'][0]['al']['picUrl']+"?param=300x300"
            await app.sendGroupMessage(group, MessageChain.create([
                Image_NetworkAddress(music_al),
                Plain(f"\n曲名：{music_name}\n作者：{music_ar}"),
                Plain("\n超过9:00的歌曲将被裁切前9:00\n歌曲时长越长音质越差\n超过4分钟的歌曲音质将受到较大程度的损伤\n发送语音需要一定时间，请耐心等待")
            ]))

        cache = Path(f'{MIRAI_PATH}data/net.mamoe.mirai-api-http/voices/{musicid}')
        cache.write_bytes(await silkcoder.encode(f'./saya/CloudMusic/temp/{musicid}.mp3', t=540))
        await app.sendGroupMessage(group, MessageChain.create([Voice(path=musicid)]))
        # os.remove(f'{MIRAI_PATH}data/net.mamoe.mirai-api-http/voices/{musicid}')
        return WAITING.remove(member.id)


@channel.use(ListenerSchema(listening_events=[FriendMessage], inline_dispatchers=[Literature("查看点歌状态")]))
async def main(app: GraiaMiraiApplication, friend: Friend):
    if friend.id == yaml_data['Basic']['Permission']['Master']:
        runlist_len = len(WAITING)
        runlist = "\n".join(map(lambda x: str(x), WAITING))
        if runlist_len > 0:
            await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
                Plain(f"当前共有 {runlist_len} 人正在点歌"),
                Plain(f"\n{runlist}")
            ]))
        else:
            await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([Plain(f"当前没有正在点歌的人")]))
