import os
import json
import time
import requests

from graiax import silkcoder
from graia.saya import Saya, Channel
from graia.application.event.messages import *
from graia.application import GraiaMiraiApplication
from graia.application.message.elements.internal import *
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.parser.literature import Literature
from graia.broadcast.interrupt import InterruptControl
from graia.broadcast.interrupt.waiter import Waiter

from config import yaml_data, group_data, sendmsg


saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
inc = InterruptControl(bcc)

if not os.path.exists("./saya/CloudMusic/temp/"):
    print("正在创建音乐缓存文件夹")
    os.mkdir("./saya/CloudMusic/temp/")

HOST = "http://127.0.0.1:3000"
if not yaml_data['Saya']['CloudMusic']['Disabled']:
    phone = yaml_data['Saya']['CloudMusic']['ApiConfig']['PhoneNumber']
    password = yaml_data['Saya']['CloudMusic']['ApiConfig']['Password']
    login = requests.get(f"{HOST}/login/cellphone?phone={phone}&password={password}").cookies

WAITING = []


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("点歌")]))
async def what_are_you_saying(app: GraiaMiraiApplication, group: Group, member: Member):

    if yaml_data['Saya']['CloudMusic']['Disabled']:
        return await sendmsg(app=app, group=group)
    elif 'CloudMusic' in group_data[group.id]['DisabledFunc']:
        return await sendmsg(app=app, group=group)

    if member.id in WAITING:
        waite_musicmessageId = await app.sendGroupMessage(group, MessageChain.create([Plain(f"请发送歌曲名，发送取消即可终止点歌")]))
        WAITING.append(member.id)
        @Waiter.create_using_function([GroupMessage])
        async def waiter1(waiter1_group: Group, waiter1_member: Member, waiter1_message: MessageChain):
            if all([waiter1_group.id == group.id,
                waiter1_member.id == member.id]):
                waiter1_saying = waiter1_message.asDisplay()
                return waiter1_saying
        try:
            message = await asyncio.wait_for(inc.wait(waiter1), timeout=15)
            if message == "取消":
                WAITING.remove(member.id)
                return await app.sendGroupMessage(group, MessageChain.create([Plain("已取消点歌")]))
            else:
                times = str(int(time.time()))
                print()
                search = requests.get(
                    url=f"{HOST}/cloudsearch?keywords={message}&timestamp={times}", cookies=login)
                musiclist = json.loads(search.text)["result"]["songs"]
                msg = []
                musicIdList = []
                msg.append(Plain(f"为你在网易云音乐找到以下歌曲！"))
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
                    msg.append(Plain(f"\n{num} ---> {music_name} - {music_ar}"))
                    musicIdList.append(music_id)
                    num += 1
                msg.append(Plain(f"\n发送歌曲id可完成点歌\n发送取消可终止当前点歌"))
                await app.sendGroupMessage(group, MessageChain.create(msg))

                @Waiter.create_using_function([GroupMessage])
                async def waiter2(waiter2_group: Group, waiter2_member: Member, waiter2_message: MessageChain):
                    if all([waiter2_group.id == group.id,
                            waiter2_member.id == member.id]):
                        return waiter2_message.asDisplay()
                try:
                    wantMusicID = await asyncio.wait_for(inc.wait(waiter2), timeout=15)
                    if wantMusicID == "取消":
                        WAITING.remove(member.id)
                        return await app.sendGroupMessage(group, MessageChain.create([Plain("已取消点歌")]))
                    elif wantMusicID not in ["1", "2", "3", "4", "5", "6", "7", "8", "8", "10"]:
                        await app.sendGroupMessage(group, MessageChain.create([Plain("请发送歌曲 id<1-10> 来点歌")]))
                    else:
                        musicid = musicIdList[int(wantMusicID) - 1]
                        times = str(int(time.time()))
                        musicinfo = requests.get(
                            url=f"{HOST}/song/detail?ids={musicid}&timestamp={times}",
                            cookies=login).json()
                        musicurl = requests.get(
                            url=f"{HOST}/song/url?id={musicid}&br=128000&timestamp={times}",
                            cookies=login).json()
                        if yaml_data['Saya']['CloudMusic']['MusicInfo']:
                            music_name = musicinfo['songs'][0]['name']
                            music_ar = []
                            for ar in musicinfo['songs'][0]['ar']:
                                music_ar.append(ar['name'])
                            music_ar = "/".join(music_ar)
                            music_al = musicinfo['songs'][0]['al']['picUrl']+"?param=200x200"
                            await app.sendGroupMessage(group, MessageChain.create([
                                Image_NetworkAddress(music_al),
                                Plain(f"\n曲名：{music_name}\n作者：{music_ar}")]))
                        if not os.path.exists(f"./saya/CloudMusic/temp/{musicid}.silk"):
                            music_url = musicurl["data"][0]["url"]
                            r = requests.get(music_url)
                            music_fcontent = r.content
                            with open(f'./saya/CloudMusic/temp/{musicid}.mp3', 'wb') as f:
                                f.write(music_fcontent)
                            await ffmpeg(f"ffmpeg -i ./saya/CloudMusic/temp/{musicid}.mp3 -ss 00:00:00 -t 00:02:00 -f wav ./saya/CloudMusic/temp/{musicid}.wav -y")
                            await silkcoder.encode(f'./saya/CloudMusic/temp/{musicid}.wav', f'./saya/CloudMusic/temp/{musicid}.silk')
                            os.remove(f'./saya/CloudMusic/temp/{musicid}.mp3')
                            os.remove(f'./saya/CloudMusic/temp/{musicid}.wav')
                        await app.sendGroupMessage(group, MessageChain.create([Voice_LocalFile(f"./saya/CloudMusic/temp/{musicid}.silk")]))
                        return WAITING.remove(member.id)

                except asyncio.TimeoutError:
                    WAITING.remove(member.id)
                    return await app.sendGroupMessage(group, MessageChain.create([
                        Plain("点歌超时")
                    ]), quote=waite_musicmessageId.messageId)

        except asyncio.TimeoutError:
            WAITING.remove(member.id)
            return await app.sendGroupMessage(group, MessageChain.create([
                Plain("点歌超时")
            ]), quote=waite_musicmessageId.messageId)


async def ffmpeg(shell):
    os.system(shell)