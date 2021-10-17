import os
import time
import asyncio

import xmltodict

from pathlib import Path
from graiax import silkcoder
from graia.saya import Saya, Channel
from graia.application.group import Member
from concurrent.futures import ThreadPoolExecutor
from graia.application import GraiaMiraiApplication
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.event.messages import Group, GroupMessage
from graia.application.message.parser.literature import Literature
from graia.application.message.elements.internal import Plain, MessageChain, Voice, Source
from azure.cognitiveservices.speech import AudioDataStream, SpeechConfig, SpeechSynthesizer


from datebase.db import reduce_gold
from util.limit import member_limit_check
from util.RestControl import rest_control
from util.UserBlock import group_black_list_block
from config import yaml_data, group_data, VIOCE_PATH

saya = Saya.current()
channel = Channel.current()

TTSRUNING = False

BASEPATH = Path(__file__).parent.joinpath("temp")
BASEPATH.mkdir(exist_ok=True)

@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Literature("/tts")],
                            headless_decorators=[rest_control(), member_limit_check(40), group_black_list_block()]))
async def azuretts(app: GraiaMiraiApplication, group: Group, member: Member, message: MessageChain, source: Source):

    if yaml_data['Saya']['AzureTTS']['Disabled']:
        return
    elif 'AzureTTS' in group_data[group.id]['DisabledFunc']:
        return

    saying = message.asDisplay().split(" ", 3)
    if len(saying) != 4:
        return await app.sendGroupMessage(group, MessageChain.create([Plain("格式有误：/tts <性别> <感情> <文字>")]))

    if saying[1] == "男":
        name = "Microsoft Server Speech Text to Speech Voice (zh-CN, YunxiNeural)"
        style_list = ["助理", "平静", "害怕", "开心", "不满",
                      "严肃", "生气", "悲伤", "沮丧", "尴尬", "默认"]
        if saying[2] not in style_list:
            style_list_str = "、".join(style_list)
            return await app.sendGroupMessage(group, MessageChain.create([Plain(f"该性别可使用的感情：{style_list_str}")]))
    elif saying[1] == "女":
        name = "Microsoft Server Speech Text to Speech Voice (zh-CN, XiaoxiaoNeural)"
        style_list = ["助理", "聊天", "客服", "新闻", "撒娇", "生气", "平静",
                      "开心", "不满", "害怕", "温柔", "抒情", "悲伤", "严肃", "默认"]
        if saying[2] not in style_list:
            style_list_str = "、".join(style_list)
            return await app.sendGroupMessage(group, MessageChain.create([Plain(f"该性别可使用的感情：{style_list_str}")]))
    else:
        return await app.sendGroupMessage(group, MessageChain.create([Plain("性别仅支持【男/女】")]))

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
        return await app.sendGroupMessage(group, MessageChain.create([Plain("你的游戏币不足，无法请求语音")]), quote=source)

    if TTSRUNING:
        return app.sendGroupMessage(group, MessageChain.create([Plain("当前tts队列已满，请等待")]), quote=source)

    if len(saying[3]) < 800:
        times = str(int(time.time() * 100))
        voicefile = BASEPATH.joinpath(f"{times}.wav")

        loop = asyncio.get_event_loop()
        pool = ThreadPoolExecutor(5)
        await loop.run_in_executor(pool, gettts, name, style, saying[3], voicefile.__str__())
        cache = VIOCE_PATH.joinpath(times)
        cache.write_bytes(await silkcoder.encode(voicefile.read_bytes(), rate=100000))
        await app.sendGroupMessage(group, MessageChain.create([Voice(path=times)]))
        voicefile.unlink()
        cache.unlink()
    else:
        await app.sendGroupMessage(group, MessageChain.create([Plain("文字过长，仅支持600字以内")]))


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
                "mstts:express-as": {
                    "@style": style,
                    "#text": text
                }
            }
        }
    }
    con = xmltodict.unparse(xml_json, encoding='utf-8', pretty=1)
    print(con)
    return con


def gettts(name, style, text, voicefile):
    speech_config = SpeechConfig(subscription=yaml_data["Saya"]["AzureTTS"]["Subscription"],
                                 region=yaml_data["Saya"]["AzureTTS"]["Region"])
    synthesizer = SpeechSynthesizer(
        speech_config=speech_config, audio_config=None)
    ssml_string = dict2xml(name, style, text)
    result = synthesizer.speak_ssml_async(ssml_string).get()
    stream = AudioDataStream(result)
    stream.save_to_wav_file(voicefile)
