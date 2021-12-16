import time
import asyncio
import xmltodict

from pathlib import Path
from graiax import silkcoder
from graia.saya import Saya, Channel
from graia.ariadne.model import Member, Group
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Voice, Source
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import Twilight, FullMatch, WildcardMatch
from azure.cognitiveservices.speech import (
    SpeechConfig,
    AudioDataStream,
    SpeechSynthesizer,
)

from database.db import reduce_gold
from util.sendMessage import safeSendGroupMessage
from util.control import Permission, Interval, Rest
from config import yaml_data, group_data, COIN_NAME

saya = Saya.current()
channel = Channel.current()

BASEPATH = Path(__file__).parent.joinpath("temp")
BASEPATH.mkdir(exist_ok=True)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                {"head": FullMatch("/tts"), "anything": WildcardMatch(optional=True)}
            )
        ],
        decorators=[Rest.rest_control(), Permission.require(), Interval.require(60)],
    )
)
async def azuretts(group: Group, member: Member, message: MessageChain, source: Source):

    if (
        yaml_data["Saya"]["AzureTTS"]["Disabled"]
        and group.id != yaml_data["Basic"]["Permission"]["DebugGroup"]
    ):
        return
    elif "AzureTTS" in group_data[str(group.id)]["DisabledFunc"]:
        return

    saying = message.asDisplay().split(" ", 3)
    if len(saying) != 4:
        return await safeSendGroupMessage(
            group, MessageChain.create([Plain("格式有误：/tts <性别> <感情> <文字>")])
        )

    if saying[1] == "男":
        name = "Microsoft Server Speech Text to Speech Voice (zh-CN, YunxiNeural)"
        style_list = ["助理", "平静", "害怕", "开心", "不满", "严肃", "生气", "悲伤", "沮丧", "尴尬", "默认"]
        if saying[2] not in style_list:
            style_list_str = "、".join(style_list)
            return await safeSendGroupMessage(
                group, MessageChain.create([Plain(f"该性别可使用的感情：{style_list_str}")])
            )
    elif saying[1] == "女":
        name = "Microsoft Server Speech Text to Speech Voice (zh-CN, XiaoxiaoNeural)"
        style_list = [
            "助理",
            "聊天",
            "客服",
            "新闻",
            "撒娇",
            "生气",
            "平静",
            "开心",
            "不满",
            "害怕",
            "温柔",
            "抒情",
            "悲伤",
            "严肃",
            "默认",
        ]
        if saying[2] not in style_list:
            style_list_str = "、".join(style_list)
            return await safeSendGroupMessage(
                group, MessageChain.create([Plain(f"该性别可使用的感情：{style_list_str}")])
            )
    else:
        return await safeSendGroupMessage(
            group, MessageChain.create([Plain("性别仅支持【男/女】")])
        )

    if saying[2] == "默认":
        style = "Default"
    elif saying[2] == "助理":
        style = "assistant"
    elif saying[2] == "聊天":
        style = "chat"
    elif saying[2] == "客服":
        style = "customerservice"
    elif saying[2] == "新闻":
        style = "newscast"
    elif saying[2] == "撒娇":
        style = "affectionate"
    elif saying[2] == "生气":
        style = "angry"
    elif saying[2] == "平静":
        style = "calm"
    elif saying[2] == "开心":
        style = "cheerful"
    elif saying[2] == "不满":
        style = "disgruntled"
    elif saying[2] == "害怕":
        style = "fearful"
    elif saying[2] == "温柔":
        style = "gentle"
    elif saying[2] == "抒情":
        style = "lyrical"
    elif saying[2] == "悲伤":
        style = "sad"
    elif saying[2] == "严肃":
        style = "serious"
    elif saying[2] == "沮丧":
        style = "depressed"
    elif saying[2] == "尴尬":
        style = "embarrassed"

    if not await reduce_gold(str(member.id), 2):
        return await safeSendGroupMessage(
            group,
            MessageChain.create([Plain(f"你的{COIN_NAME}不足，无法请求语音")]),
            quote=source.id,
        )

    if len(saying[3]) < 800:
        times = str(int(time.time() * 100))
        voicefile = BASEPATH.joinpath(f"{times}.wav")
        await asyncio.to_thread(gettts, name, style, saying[3], str(voicefile))
        vioce_bytes = await silkcoder.encode(voicefile.read_bytes())
        await safeSendGroupMessage(
            group, MessageChain.create([Voice(data_bytes=vioce_bytes)])
        )
        voicefile.unlink()
    else:
        await safeSendGroupMessage(
            group, MessageChain.create([Plain("文字过长，仅支持600字以内")])
        )


def dict2xml(name: str, style: str, text: str):
    xml_json = {
        "speak": {
            "@xmlns": "http://www.w3.org/2001/10/synthesis",
            "@xmlns:mstts": "http://www.w3.org/2001/mstts",
            "@xmlns:emo": "http://www.w3.org/2009/10/emotionml",
            "@version": "1.0",
            "@xml:lang": "zh-CN",
            "voice": {
                "@name": name,
                "mstts:express-as": {"@style": style, "#text": text},
            },
        }
    }
    con = xmltodict.unparse(xml_json, encoding="utf-8", pretty=1)
    return con


def gettts(name, style, text, voicefile):
    speech_config = SpeechConfig(
        subscription=yaml_data["Saya"]["AzureTTS"]["Subscription"],
        region=yaml_data["Saya"]["AzureTTS"]["Region"],
    )
    synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=None)
    ssml_string = dict2xml(name, style, text)
    result = synthesizer.speak_ssml_async(ssml_string).get()
    stream = AudioDataStream(result)
    stream.save_to_wav_file(voicefile)
