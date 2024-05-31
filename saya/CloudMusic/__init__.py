import time
import httpx
import asyncio

from pathlib import Path

from loguru import logger
from graiax import silkcoder
from graia.saya import Channel, Saya
from graia.ariadne.model import Group, Member
from graia.broadcast.interrupt.waiter import Waiter
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import GroupMessage
from graia.broadcast.interrupt import InterruptControl
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.element import Image, Plain, Source, Voice
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    RegexResult,
    WildcardMatch,
)

from database.db import reduce_gold
from config import COIN_NAME, yaml_data
from util.text2image import create_image
from util.sendMessage import safeSendGroupMessage
from util.control import Function, Interval, Permission, Rest

saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
inc = InterruptControl(bcc)

BASEPATH = Path(__file__).parent.joinpath("temp")
BASEPATH.mkdir(exist_ok=True)

CLOUD_HOST = "http://127.0.0.1:3000"
QQ_HOST = "http://127.0.0.1:3200"

if not yaml_data["Saya"]["CloudMusic"]["Disabled"]:
    phone = yaml_data["Saya"]["CloudMusic"]["ApiConfig"]["PhoneNumber"]
    password = yaml_data["Saya"]["CloudMusic"]["ApiConfig"]["Password"]
    try:
        login = httpx.get(
            f"{CLOUD_HOST}/login/cellphone?phone={phone}&password={password}"
        ).cookies
        logger.info("网易云音乐登录成功")
    except httpx.ConnectError:
        logger.error(
            "无法连接网易云音乐后端，请检查是否完成搭建并成功启动 https://github.com/Binaryify/NeteaseCloudMusicApi"
        )
        exit(1)
    # try:
    #     httpx.get(QQ_HOST)
    #     logger.info("QQ音乐登录成功")
    # except httpx.ConnectError:
    #     logger.error("无法连接QQ音乐后端，请检查是否完成搭建并成功启动 https://github.com/Rain120/qq-music-api")
    #     exit(1)

WAITING = []


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([FullMatch("点歌"), "music_name" @ WildcardMatch(optional=True)]),
        ],
        decorators=[
            Function.require("CloudMusic"),
            Permission.require(),
            Rest.rest_control(),
            Interval.require(120),
        ],
    )
)
async def sing(
    group: Group,
    member: Member,
    source: Source,
    music_name: RegexResult,
):
    @Waiter.create_using_function(
        listening_events=[GroupMessage], using_decorators=[Permission.require()]
    )
    async def waiter1(
        waiter1_group: Group, waiter1_member: Member, waiter1_message: MessageChain
    ):
        if all([waiter1_group.id == group.id, waiter1_member.id == member.id]):
            waiter1_saying = waiter1_message.asDisplay()
            if waiter1_saying == "取消":
                return False
            elif waiter1_saying.replace(" ", "") == "":
                await safeSendGroupMessage(group, MessageChain.create([Plain("请不要输入空格")]))
            else:
                return waiter1_saying

    @Waiter.create_using_function(
        listening_events=[GroupMessage], using_decorators=[Permission.require()]
    )
    async def waiter2(
        waiter2_group: Group, waiter2_member: Member, waiter2_message: MessageChain
    ):
        if all([waiter2_group.id == group.id, waiter2_member.id == member.id]):
            if waiter2_message.asDisplay() == "取消":
                return False
            elif waiter2_message.asDisplay() in [
                "1",
                "2",
                "3",
                "4",
                "5",
                "6",
                "7",
                "8",
                "9",
                "10",
                "11",
                "12",
                "13",
                "14",
                "15",
                "16",
                "17",
                "18",
                "19",
                "20",
            ]:
                return waiter2_message.asDisplay()
            else:
                await safeSendGroupMessage(
                    group,
                    MessageChain.create([Plain("请发送歌曲 id<1-10> 来点歌，发送取消可终止本次点歌")]),
                )

    if member.id not in WAITING:
        WAITING.append(member.id)

        if music_name.matched:
            musicname = music_name.result.getFirst(Plain).text
            if musicname is None or musicname.replace(" ", "") == "":
                WAITING.remove(member.id)
                return await safeSendGroupMessage(
                    group, MessageChain.create([Plain("歌名输入有误")])
                )
        else:
            waite_musicmessageId = await safeSendGroupMessage(
                group, MessageChain.create([Plain("请发送歌曲名，发送取消即可终止点歌")])
            )
            try:
                musicname = await asyncio.wait_for(inc.wait(waiter1), timeout=30)
                if not musicname:
                    WAITING.remove(member.id)
                    return await safeSendGroupMessage(
                        group, MessageChain.create([Plain("已取消点歌")])
                    )
            except asyncio.TimeoutError:
                WAITING.remove(member.id)
                return await safeSendGroupMessage(
                    group,
                    MessageChain.create([Plain("点歌超时")]),
                    quote=waite_musicmessageId.messageId,
                )

        notfound = 0
        msg = ""

        times = str(int(time.time()))
        search = httpx.get(
            f"{CLOUD_HOST}/cloudsearch?keywords={musicname}&timestamp={times}",
            cookies=login,
        ).json()
        if search["result"].get("songCount", 0) == 0:
            notfound += 1
        else:
            musiclist = search["result"]["songs"]
            musicIdList = []
            num = 1
            i = 1

            msg = "===============================\n为你在网易云音乐找到以下歌曲！\n==============================="
            for music in musiclist:
                if num > 10:
                    break
                music_id = music["id"]
                music_name = music["name"]
                music_ar = []
                for ar in music["ar"]:
                    music_ar.append(ar["name"])
                music_ar = "/".join(music_ar)
                num_str = " " + str(i) if i < 10 else str(i)
                msg += f"\n{num_str}    ===>    {music_name} - {music_ar}"
                musicIdList.append([1, music_id])
                num += 1
                i += 1

        # for _ in range(3):
        #     try:
        #         async with httpx.AsyncClient() as client:
        #             resp = await client.get(f"{QQ_HOST}/getSearchByKey?key={musicname}")
        #             search = resp.json()
        #             break
        #     except Exception:
        #         logger.error("QQ Music API 连接出错，正在重试")
        #         await asyncio.sleep(0.5)
        # else:
        #     WAITING.remove(member.id)
        #     return await safeSendGroupMessage(
        #         group, MessageChain.create([Plain("QQ Music API 连接出错")])
        #     )
        # if search["response"]["data"]["song"]["curnum"] == 0:
        #     notfound += 1
        # else:
        #     musiclist = search["response"]["data"]["song"]["list"]
        #     num = 1
        #     msg += "\n===============================\n为你在QQ音乐找到以下歌曲！\n==============================="
        #     for music in musiclist:
        #         if num > 10:
        #             break
        #         music_id = music["songmid"]
        #         music_name = music["songname"]
        #         music_ar = []
        #         for ar in music["singer"]:
        #             music_ar.append(ar["name"])
        #         music_ar = "/".join(music_ar)
        #         num_str = " " + str(i) if i < 10 else str(i)
        #         msg += f"\n{num_str}    ===>    {music_name} - {music_ar}"
        #         musicIdList.append([2, music_id])
        #         num += 1
        #         i += 1

        if notfound == 2:
            WAITING.remove(member.id)
            return await safeSendGroupMessage(
                group, MessageChain.create([Plain("未找到此歌曲")])
            )

        msg += (
            "\n===============================\n"
            f"发送歌曲id可完成点歌\n发送取消可终止当前点歌\n点歌将消耗 4 个{COIN_NAME}\n"
            "==============================="
        )
        image = await create_image(msg)
        waite_musicmessageId = await safeSendGroupMessage(
            group, MessageChain.create([Image(data_bytes=image)])
        )

        try:
            wantMusicID = await asyncio.wait_for(inc.wait(waiter2), timeout=30)
            if not wantMusicID:
                WAITING.remove(member.id)
                return await safeSendGroupMessage(
                    group, MessageChain.create([Plain("已取消点歌")])
                )
        except asyncio.TimeoutError:
            WAITING.remove(member.id)
            return await safeSendGroupMessage(
                group,
                MessageChain.create([Plain("点歌超时")]),
                quote=waite_musicmessageId.messageId,
            )

        try:
            musicid = musicIdList[int(wantMusicID) - 1]
        except IndexError:
            WAITING.remove(member.id)
            return await safeSendGroupMessage(group, MessageChain.create("输入有误"))
        if musicid[0] == 1:
            times = str(int(time.time()))
            musicinfo = httpx.get(
                url=f"{CLOUD_HOST}/song/detail?ids={musicid[1]}&timestamp={times}",
                cookies=login,
            ).json()
            musicurl = httpx.get(
                url=f"{CLOUD_HOST}/song/url?id={musicid[1]}&br=128000&timestamp={times}",
                cookies=login,
            ).json()["data"][0]["url"]
            if yaml_data["Saya"]["CloudMusic"]["MusicInfo"]:
                music_name = musicinfo["songs"][0]["name"]
                music_ar = []
                for ar in musicinfo["songs"][0]["ar"]:
                    music_ar.append(ar["name"])
                music_ar = "/".join(music_ar)
                music_al = musicinfo["songs"][0]["al"]["picUrl"] + "?param=300x300"
            musiclyric = httpx.get(
                f"{CLOUD_HOST}/lyric?id={musicid[1]}&timestamp={times}"
            ).json()
            music_lyric = musiclyric.get("lrc", {}).get("lyric", None)
        elif musicid[0] == 2:
            musicinfo = httpx.get(f"{QQ_HOST}/getSongInfo?songmid={musicid[1]}").json()[
                "response"
            ]["songinfo"]["data"]["track_info"]
            musicurl = httpx.get(f"{QQ_HOST}/getMusicPlay?songmid={musicid[1]}").json()[
                "data"
            ]["playUrl"][musicid[1]]["url"]
            album_mid = musicinfo["album"]["mid"]
            if yaml_data["Saya"]["CloudMusic"]["MusicInfo"]:
                music_name = musicinfo["name"]
                music_ar = []
                for ar in musicinfo["singer"]:
                    music_ar.append(ar["name"])
                music_ar = "/".join(music_ar)
                music_al = httpx.get(f"{QQ_HOST}/getImageUrl?id={album_mid}").json()[
                    "response"
                ]["data"]["imageUrl"]
            musiclyric = httpx.get(f"{QQ_HOST}/getLyric?songmid={musicid[1]}").json()
            music_lyric = musiclyric["response"].get("lyric", "")
            if music_lyric == "[00:00:00]此歌曲为没有填词的纯音乐，请您欣赏" or music_lyric == "":
                music_lyric = None

        MUSIC_PATH = BASEPATH.joinpath(f"{musicid[1]}.mp3")
        if not MUSIC_PATH.exists():
            logger.info(f"正在缓存歌曲：{music_name}")
            if musicurl is None or musicurl == "":
                WAITING.remove(member.id)
                return await safeSendGroupMessage(
                    group,
                    MessageChain.create([Plain(f"该歌曲（{music_name}）由于版权问题无法点歌，请使用客户端播放")]),
                )
            async with httpx.AsyncClient() as client:
                for _ in range(3):
                    try:
                        r = await client.get(musicurl)
                        break
                    except Exception as e:
                        logger.error(f"缓存歌曲失败：{e}")
                        await asyncio.sleep(1)
                else:
                    await safeSendGroupMessage(
                        group,
                        MessageChain.create([Plain(f"该歌曲（{music_name}）缓存失败，请稍后重试")]),
                    )
                    WAITING.remove(member.id)
                    return
                MUSIC_PATH.write_bytes(r.content)

        if not await reduce_gold(member.id, 4):
            WAITING.remove(member.id)
            return await safeSendGroupMessage(
                group,
                MessageChain.create([Plain(f"你的{COIN_NAME}不足，无法使用")]),
                quote=source.id,
            )

        try:
            await safeSendGroupMessage(
                group,
                MessageChain.create(
                    [
                        Image(url=music_al),
                        Plain(f"\n曲名：{music_name}\n作者：{music_ar}"),
                        Plain(
                            "\n超过9:00的歌曲将被裁切前9:00\n歌曲时长越长音质越差\n超过4分钟的歌曲音质将受到较大程度的损伤\n发送语音需要一定时间，请耐心等待"
                        ),
                    ]
                ),
            )
        except Exception:
            await safeSendGroupMessage(
                group,
                MessageChain.create(
                    [
                        Plain(f"曲名：{music_name}\n作者：{music_ar}"),
                        Plain(
                            "\n超过9:00的歌曲将被裁切前9:00\n歌曲时长越长音质越差\n超过4分钟的歌曲音质将受到较大程度的损伤\n发送语音需要一定时间，请耐心等待"
                        ),
                    ]
                ),
            )

        if music_lyric:
            music_lyric_image = await create_image(music_lyric, 120)
            await safeSendGroupMessage(
                group, MessageChain.create([Image(data_bytes=music_lyric_image)])
            )

        music_bytes = await silkcoder.async_encode(MUSIC_PATH.read_bytes(), t=540)
        await safeSendGroupMessage(
            group, MessageChain.create([Voice(data_bytes=music_bytes)])
        )
        return WAITING.remove(member.id)
