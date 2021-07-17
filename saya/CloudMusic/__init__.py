import os
import json
import time
import requests

from graiax import silkcoder
from graia.saya import Saya, Channel
from graia.application.event.mirai import *
from graia.application.event.messages import *
from graia.application import GraiaMiraiApplication
from graia.application.message.elements.internal import *
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.parser.literature import Literature

from config import yaml_data, group_data, sendmsg


saya = Saya.current()
channel = Channel.current()

if not os.path.exists("./saya/CloudMusic/temp/"):
    print("正在创建音乐缓存文件夹")
    os.mkdir("./saya/CloudMusic/temp/")

HOST = "http://127.0.0.1:3000"
if not yaml_data['Saya']['CloudMusic']['Disabled']:
    phone = yaml_data['Saya']['CloudMusic']['ApiConfig']['PhoneNumber']
    password = yaml_data['Saya']['CloudMusic']['ApiConfig']['Password']
    login = requests.get(f"{HOST}/login/cellphone?phone={phone}&password={password}").cookies


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("点歌")]))
async def what_are_you_saying(app: GraiaMiraiApplication, group: Group):

    if yaml_data['Saya']['CloudMusic']['Disabled']:
        return await sendmsg(app=app, group=group)
    elif 'CloudMusic' in group_data[group.id]['DisabledFunc']:
        return await sendmsg(app=app, group=group)

    await app.sendGroupMessage(group, MessageChain.create([Plain(f"发送<搜歌 歌曲名等>即可搜歌")]))


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("搜歌")]))
async def what_are_you_saying(app: GraiaMiraiApplication, group: Group, saying: MessageChain):

    if yaml_data['Saya']['CloudMusic']['Disabled']:
        return await sendmsg(app=app, group=group)
    elif 'CloudMusic' in group_data[group.id]['DisabledFunc']:
        return await sendmsg(app=app, group=group)

    if len(saying.asDisplay().split()) == 1:
        return await app.sendGroupMessage(group, MessageChain.create([Plain(f"发送<搜歌 歌曲名等>即可搜歌")]))
    message = saying.asDisplay().split(" ", 1)
    times = str(int(time.time()))
    search = requests.get(
        url=f"{HOST}/cloudsearch?keywords={message[1]}&timestamp={times}", cookies=login)
    musiclist = json.loads(search.text)["result"]["songs"]
    msg = []
    msg.append(Plain(f"为你在网易云音乐找到以下歌曲！\n发送 <唱歌 id> 即可完成点歌"))
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
        msg.append(Plain(f"\n{music_id} ---> {music_name} - {music_ar}"))
        num += 1
    await app.sendGroupMessage(group, MessageChain.create(msg))


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("唱歌")]))
async def what_are_you_saying(app: GraiaMiraiApplication, group: Group, saying: MessageChain):

    if yaml_data['Saya']['CloudMusic']['Disabled']:
        return await sendmsg(app=app, group=group)
    elif 'CloudMusic' in group_data[group.id]['DisabledFunc']:
        return await sendmsg(app=app, group=group)

    if len(saying.asDisplay().split()) == 1:
        return await app.sendGroupMessage(group, MessageChain.create([Plain(f"请发送 <唱歌 歌曲id>")]))

    musicid = saying.asDisplay().split()[1]
    times = str(int(time.time()))
    musiccheck = json.loads(requests.get(
        url=f"{HOST}/check/music?id={musicid}&timestamp={times}", cookies=login).text)
    print(musiccheck)
    # if musiccheck['message'] == "ok":
    musicinfo = requests.get(
        url=f"{HOST}/song/detail?ids={musicid}&timestamp={times}", cookies=login).text
    print(musicinfo)
    musicinfo = json.loads(musicinfo)
    musicurl = json.loads(requests.get(
        url=f"{HOST}/song/url?id={musicid}&br=128000&timestamp={times}", cookies=login).text)
    if yaml_data['Saya']['CloudMusic']['MusicInfo']:
        music_name = musicinfo['songs'][0]['name']
        music_ar = []
        for ar in musicinfo['songs'][0]['ar']:
            music_ar.append(ar['name'])
        music_ar = "/".join(music_ar)
        music_al = musicinfo['songs'][0]['al']['picUrl']
        await app.sendGroupMessage(group,
                                   MessageChain.create([Image_NetworkAddress(music_al),
                                                        Plain(f"\n曲名：{music_name}\n作者：{music_ar}")]))
    if not os.path.exists(f"./saya/CloudMusic/temp/{musicid}.silk"):
        music_url = musicurl["data"][0]["url"]
        r = requests.get(music_url)
        music_fcontent = r.content
        with open(f'./saya/CloudMusic/temp/{musicid}.mp3', 'wb') as f:
            f.write(music_fcontent)
        os.system(
            f"ffmpeg -i ./saya/CloudMusic/temp/{musicid}.mp3 -ss 00:00:00 -t 00:02:00 -f wav ./saya/CloudMusic/temp/{musicid}.wav -y")
        await silkcoder.encode(f'./saya/CloudMusic/temp/{musicid}.wav', f'./saya/CloudMusic/temp/{musicid}.silk')
        os.remove(f'./saya/CloudMusic/temp/{musicid}.mp3')
        os.remove(f'./saya/CloudMusic/temp/{musicid}.wav')
    await app.sendGroupMessage(group, MessageChain.create([Voice_LocalFile(f"./saya/CloudMusic/temp/{musicid}.silk")]))
    # await app.sendGroupMessage(group, MessageChain.create([Plain(f"该歌曲无法播放\n{musiccheck['message']}")]))
