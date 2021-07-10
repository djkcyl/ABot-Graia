import json
import httpx
import asyncio

from config import yaml_data

from .get_token import get_token


async def post_text(text, type):
    token = get_token()
    post_url = "https://nls-gateway.cn-shanghai.aliyuncs.com/rest/v1/tts/async"
    body_json = {
        "payload": {
            "tts_request": {
                "voice": type,
                "sample_rate": 16000,
                "format": "wav",
                "text": text,
                "enable_subtitle": True
            },
            "enable_notify": False
        },
        "context": {
            "device_id": yaml_data['Basic']['BotName']
        },
        "header": {
            "appkey": yaml_data['Saya']['AliTTS']['Appkey'],
            "token": token
        }
    }
    tts_body = json.loads(httpx.post(post_url, json=body_json).text)
    print(tts_body)
    error_message = tts_body['error_message']
    task_id = tts_body['data']['task_id']
    print(error_message)
    return await waitloop_url(token, task_id)


async def waitloop_url(token, task_id):
    s = 1
    url = f"https://nls-gateway.cn-shanghai.aliyuncs.com/rest/v1/tts/async?appkey={yaml_data['Saya']['AliTTS']['Appkey']}&token={token}&task_id={task_id}"
    while s < 100:
        tts_url_get = json.loads(httpx.get(url).text)
        if (tts_url_get["error_code"] == 20000000) and (tts_url_get["error_message"] == "SUCCESS"):
            return tts_url_get["data"]["audio_address"]
        else:
            await asyncio.sleep(1)
        s += 1
