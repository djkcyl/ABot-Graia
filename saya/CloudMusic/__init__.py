import os
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
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.parser.literature import Literature
from graia.application.event.messages import FriendMessage, GroupMessage
from graia.application.message.elements.internal import Image_UnsafeBytes, MessageChain, Plain, Image_NetworkAddress, Voice, Source

from datebase.db import reduce_gold
from util.aiorequests import aiorequests
from util.text2image import create_image
from util.limit import member_limit_check
from util.RestControl import rest_control
from util.UserBlock import black_list_block
from config import yaml_data, group_data, sendmsg

saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
inc = InterruptControl(bcc)

if not os.path.exists("./saya/CloudMusic/temp/"):
    print("正在创建音乐缓存文件夹")
    os.mkdir("./saya/CloudMusic/temp/")

MIRAI_PATH = "/A60/bot/"

if MIRAI_PATH[-1] != "/":
    MIRAI_PATH += "/"

if not os.path.exists(f"{MIRAI_PATH}data/net.mamoe.mirai-api-http/voices/"):
    print("请打开./saya/CloudMusic/__init__.py 并修改变量 MIRAI_PATH 的内容为Mirai的根目录")
    exit()

CLOUD_HOST = "http://127.0.0.1:3000"
if not yaml_data['Saya']['CloudMusic']['Disabled']:
    phone = yaml_data['Saya']['CloudMusic']['ApiConfig']['PhoneNumber']
    password = yaml_data['Saya']['CloudMusic']['ApiConfig']['Password']
    login = requests.get(f"{CLOUD_HOST}/login/cellphone?phone={phone}&password={password}").cookies

QQ_HOST = "http://127.0.0.1:3200"

WAITING = []


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Literature("点歌")],
                            headless_decorators=[rest_control(), member_limit_check(300), black_list_block()]))
async def sing(app: GraiaMiraiApplication, group: Group, member: Member, message: MessageChain, source: Source):

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
            elif waiter1_saying.replace(" ", "") == "":
                await app.sendGroupMessage(group, MessageChain.create([Plain("请不要输入空格")]))
            else:
                return waiter1_saying

    @Waiter.create_using_function([GroupMessage])
    async def waiter2(waiter2_group: Group, waiter2_member: Member, waiter2_message: MessageChain):
        if all([waiter2_group.id == group.id, waiter2_member.id == member.id]):
            if waiter2_message.asDisplay() == "取消":
                return False
            elif waiter2_message.asDisplay() in [
                    "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20"]:
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
            if musicname == None or musicname.replace(" ", "") == "":
                WAITING.remove(member.id)
                return await app.sendGroupMessage(group, MessageChain.create([Plain("歌名输入有误")]))
        times = str(int(time.time()))
        search = requests.get(f"{CLOUD_HOST}/cloudsearch?keywords={musicname}&timestamp={times}", cookies=login).json()
        if search["result"]["songCount"] == 0:
            WAITING.remove(member.id)
            return await app.sendGroupMessage(group, MessageChain.create([Plain("未找到此歌曲")]))
        musiclist = search["result"]["songs"]
        musicIdList = []
        num = 1
        i = 1

        msg = "===============================\n为你在网易云音乐找到以下歌曲！\n==============================="
        for music in musiclist:
            if num > 10:
                break
            music_id = music['id']
            music_name = music['name']
            music_ar = []
            for ar in music['ar']:
                music_ar.append(ar['name'])
            music_ar = "/".join(music_ar)
            num_str = " " + str(i) if i < 10 else str(i)
            msg += f"\n{num_str}    ===>    {music_name} - {music_ar}"
            musicIdList.append([1, music_id])
            num += 1
            i += 1

        search = requests.get(f"{QQ_HOST}/getSearchByKey?key={musicname}").json()
        if search["response"]["data"]["song"]["curnum"] == 0:
            WAITING.remove(member.id)
            return await app.sendGroupMessage(group, MessageChain.create([Plain("未找到此歌曲")]))
        musiclist = search["response"]["data"]["song"]["list"]
        num = 1
        msg += "\n===============================\n为你在QQ音乐找到以下歌曲！\n==============================="
        for music in musiclist:
            if num > 10:
                break
            music_id = music['mid']
            music_name = music['name']
            music_ar = []
            for ar in music['singer']:
                music_ar.append(ar['name'])
            music_ar = "/".join(music_ar)
            num_str = " " + str(i) if i < 10 else str(i)
            msg += f"\n{num_str}    ===>    {music_name} - {music_ar}"
            musicIdList.append([2, music_id])
            num += 1
            i += 1

        msg += f"\n===============================\n发送歌曲id可完成点歌\n发送取消可终止当前点歌\n点歌将消耗 4 个游戏币\n==============================="
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
        if musicid[0] == 1:
            times = str(int(time.time()))
            musicinfo = requests.get(
                url=f"{CLOUD_HOST}/song/detail?ids={musicid[1]}&timestamp={times}",
                cookies=login).json()
            musicurl = requests.get(
                url=f"{CLOUD_HOST}/song/url?id={musicid[1]}&br=128000&timestamp={times}",
                cookies=login).json()["data"][0]["url"]
            if yaml_data['Saya']['CloudMusic']['MusicInfo']:
                music_name = musicinfo['songs'][0]['name']
                music_ar = []
                for ar in musicinfo['songs'][0]['ar']:
                    music_ar.append(ar['name'])
                music_ar = "/".join(music_ar)
                music_al = musicinfo['songs'][0]['al']['picUrl']+"?param=300x300"
            musiclyric = requests.get(f"{CLOUD_HOST}/lyric?id={musicid[1]}&timestamp={times}").json()
            music_lyric = musiclyric.get("lrc", False).get("lyric", None)
        elif musicid[0] == 2:
            musicinfo = requests.get(f"{QQ_HOST}/getSongInfo?songmid={musicid[1]}").json()["response"]["songinfo"]["data"]["track_info"]
            musicurl = requests.get(f"{QQ_HOST}/getMusicPlay?songmid={musicid[1]}").json()["data"]["playUrl"][musicid[1]]["url"]
            album_mid = musicinfo["album"]["mid"]
            if yaml_data['Saya']['CloudMusic']['MusicInfo']:
                music_name = musicinfo["name"]
                music_ar = []
                for ar in musicinfo["singer"]:
                    music_ar.append(ar['name'])
                    music_ar = "/".join(music_ar)
                music_al = requests.get(f"{QQ_HOST}/getImageUrl?id={album_mid}").json()["response"]["data"]["imageUrl"]
            musiclyric = requests.get(f"{QQ_HOST}/getLyric?songmid={musicid[1]}").json()
            music_lyric = musiclyric["response"]["lyric"]
            if music_lyric == "[00:00:00]此歌曲为没有填词的纯音乐，请您欣赏":
                music_lyric = None

        if not os.path.exists(f"./saya/CloudMusic/temp/{musicid[1]}.mp3"):
            print(f"正在缓存歌曲：{music_name}")
            if musicurl == None or musicurl == "":
                WAITING.remove(member.id)
                return await app.sendGroupMessage(group, MessageChain.create([Plain(f"该歌曲（{music_name}）由于版权问题无法点歌，请使用客户端播放")]))
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36 Edg/92.0.902.73"
            }
            r = await aiorequests.get(musicurl, headers=headers)
            music_fcontent = await r.content

            with open(f'./saya/CloudMusic/temp/{musicid[1]}.mp3', 'wb') as f:
                f.write(music_fcontent)

        try:
            await app.sendGroupMessage(group, MessageChain.create([
                Image_NetworkAddress(music_al),
                Plain(f"\n曲名：{music_name}\n作者：{music_ar}"),
                Plain(f"\n超过9:00的歌曲将被裁切前9:00\n歌曲时长越长音质越差\n超过4分钟的歌曲音质将受到较大程度的损伤\n发送语音需要一定时间，请耐心等待\n{musicurl}")
            ]))
        except:
            await app.sendGroupMessage(group, MessageChain.create([
                Plain(f"曲名：{music_name}\n作者：{music_ar}"),
                Plain("\n超过9:00的歌曲将被裁切前9:00\n歌曲时长越长音质越差\n超过4分钟的歌曲音质将受到较大程度的损伤\n发送语音需要一定时间，请耐心等待")
            ]))

        if music_lyric:
            music_lyric_image = await create_image(music_lyric, 120)
            await app.sendGroupMessage(group, MessageChain.create([Image_UnsafeBytes(music_lyric_image.getvalue())]))

        if not await reduce_gold(str(member.id), 4):
            WAITING.remove(member.id)
            return await app.sendGroupMessage(group, MessageChain.create([Plain("你的游戏币不足，无法使用")]), quote=source)

        cache = Path(f'{MIRAI_PATH}data/net.mamoe.mirai-api-http/voices/{musicid[1]}')
        cache.write_bytes(await silkcoder.encode(f'./saya/CloudMusic/temp/{musicid[1]}.mp3', t=540))
        await app.sendGroupMessage(group, MessageChain.create([Voice(path=musicid[1])]))
        # os.remove(f'{MIRAI_PATH}data/net.mamoe.mirai-api-http/voices/{musicid[1]}')
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
