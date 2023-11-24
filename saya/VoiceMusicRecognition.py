import json
import httpx
import asyncio

from graiax import silkcoder
from graia.saya import Channel, Saya
from graia.ariadne.model import Group, Member
from graia.broadcast.interrupt.waiter import Waiter
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.broadcast.interrupt import InterruptControl
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.element import Image, Plain, Source, Voice
from acrcloud.recognizer import ACRCloudRecognizer, ACRCloudRecognizeType
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    RegexMatch,
    RegexResult,
)

from database.db import reduce_gold
from config import COIN_NAME, yaml_data
from util.text2image import create_image
from util.sendMessage import safeSendGroupMessage
from core.control import Function, Interval, Permission

saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
inc = InterruptControl(bcc)

original_config = {
    "host": yaml_data["Saya"]["VoiceMusicRecognition"]["original"]["host"],
    "access_key": yaml_data["Saya"]["VoiceMusicRecognition"]["original"]["access_key"],
    "access_secret": yaml_data["Saya"]["VoiceMusicRecognition"]["original"][
        "access_secret"
    ],
    "recognize_type": ACRCloudRecognizeType.ACR_OPT_REC_AUDIO,
    "timeout": 15,
}
humming_config = {
    "host": yaml_data["Saya"]["VoiceMusicRecognition"]["humming"]["host"],
    "access_key": yaml_data["Saya"]["VoiceMusicRecognition"]["humming"]["access_key"],
    "access_secret": yaml_data["Saya"]["VoiceMusicRecognition"]["humming"][
        "access_secret"
    ],
    "recognize_type": ACRCloudRecognizeType.ACR_OPT_REC_HUMMING,
    "timeout": 15,
}

WAITING = []


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([FullMatch("识曲"), "operate" @ RegexMatch(r"原曲|哼唱")])
        ],
        decorators=[
            Function.require("VoiceMusicRecognition"),
            Permission.require(),
            Interval.require(30),
        ],
    )
)
async def main(group: Group, member: Member, operate: RegexResult, source: Source):
    @Waiter.create_using_function(
        listening_events=[GroupMessage], using_decorators=[Permission.require()]
    )
    async def waiter(
        waiter1_group: Group, waiter1_member: Member, waiter1_message: MessageChain
    ):
        if all([waiter1_group.id == group.id, waiter1_member.id == member.id]):
            waiter1_saying = waiter1_message.asDisplay()
            if waiter1_message.has(Voice):
                return waiter1_message.getFirst(Voice).url
            elif waiter1_saying == "取消":
                return False
            else:
                await safeSendGroupMessage(
                    group, MessageChain.create([Plain("请发送语音文件或发送取消")])
                )

    if member.id not in WAITING:
        saying = operate.result.asDisplay()
        if saying == "原曲":
            acr = ACRCloudRecognizer(original_config)
        elif saying == "哼唱":
            acr = ACRCloudRecognizer(humming_config)
        else:
            return await safeSendGroupMessage(
                group, MessageChain.create([Plain("使用方法：识曲 <原曲|哼唱>")])
            )
        WAITING.append(member.id)
        await safeSendGroupMessage(
            group,
            MessageChain.create(
                [
                    Plain(
                        f"请尽量将麦克风靠近音源后通过语音发送想要识别的歌曲，5至10秒即可，发送取消可终止识别，无论识别成功与否均需扣除 2 {COIN_NAME}"
                    )
                ]
            ),
        )
        try:
            voice_url = await asyncio.wait_for(inc.wait(waiter), timeout=60)
            if not voice_url:
                WAITING.remove(member.id)
                return await safeSendGroupMessage(
                    group, MessageChain.create([Plain("已取消识别")])
                )
        except asyncio.TimeoutError:
            WAITING.remove(member.id)
            return await safeSendGroupMessage(
                group, MessageChain.create([Plain("等待语音超时")]), quote=source.id
            )

        if await reduce_gold((member.id), 2):
            async with httpx.AsyncClient() as client:
                voice_resp = await client.get(voice_url)
            voice = voice_resp.content
            voice = await silkcoder.async_decode(voice)
            voice_info = acr.recognize_by_filebuffer(voice, 0)
            voice_info = json.loads(voice_info)
            music_list = []
            if voice_info["status"]["code"] == 0:
                i = 1
                if saying[1] == "原曲":
                    voice_info_list = voice_info["metadata"]["music"]
                else:
                    voice_info_list = voice_info["metadata"]["humming"]
                for music in voice_info_list:
                    music_name = music["title"]
                    music_artists_list = []
                    music_album = music["album"]["name"]
                    music_score = music["score"]
                    music_play_offset = int(music["play_offset_ms"] / 1000)
                    for name in music["artists"]:
                        music_artists_list.append(name["name"])
                    music_artists = " / ".join(music_artists_list)
                    music_list.append(
                        f"{i}  ====>  | {music_name} ==> {music_artists} ==> {music_album}"
                        f" | 相似度：{music_score} 播放位置：{music_play_offset} 秒"
                    )
                    i += 1
                image = await create_image(
                    str(
                        "为你找到以下可能的歌曲：   曲名 ==> 艺术家 ==> 专辑\n"
                        + "=====================================================\n"
                        + "\n".join(music_list)
                    ),
                    180,
                )
                await safeSendGroupMessage(
                    group,
                    MessageChain.create(
                        [Image(data_bytes=image), Plain(str("\n".join(music_list)))]
                    ),
                )
            elif voice_info["status"]["code"] == 1001:
                await safeSendGroupMessage(
                    group, MessageChain.create([Plain("未从语音中识别到歌曲，请检查语音音量是否过小或音质过于嘈杂")])
                )
            else:
                await safeSendGroupMessage(
                    group,
                    MessageChain.create(
                        [
                            Plain(
                                f"识别错误：{voice_info['status']['code']} {voice_info['status']['msg']}"
                            )
                        ]
                    ),
                )
        else:
            await safeSendGroupMessage(
                group, MessageChain.create([Plain(f"你的{COIN_NAME}不足，无法使用")])
            )
        WAITING.remove(member.id)
