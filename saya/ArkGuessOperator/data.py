import json
import httpx
import random
import asyncio

from lxml import etree
from pathlib import Path
from loguru import logger
from graiax.silkcoder import async_decode

DATAPATH = Path(__file__).parent.joinpath("data")
DATAPATH.mkdir(exist_ok=True)
DATAFILE = DATAPATH.joinpath("data.json")
if DATAFILE.exists():
    DATA = json.loads(DATAFILE.read_text("utf-8"))
else:
    DATA = {}
    DATAFILE.write_text(json.dumps(DATA, ensure_ascii=False, indent=4))


async def update_data():
    logger.info("[明日方舟猜干员] 正在更新数据")
    async with httpx.AsyncClient() as client:
        resp = await client.get("https://prts.wiki/w/干员一览")
        data = resp.text

        root = etree.HTML(data)
        smwdata = root.xpath('//div[@class="smwdata"]')
        logger.info(f"[明日方舟猜干员] 正在解析数据，共有{len(smwdata)}条数据")
        for smw in smwdata:
            cnname = smw.xpath("@data-cn").pop()

            if cnname not in DATA:
                DATA[cnname] = []
                logger.info(f"[明日方舟猜干员] 新增干员：{cnname}，正在更新")
            try:
                resp = await client.get(f"https://prts.wiki/w/{cnname}/语音记录")
                data = resp.text
            except httpx.HTTPError:
                logger.warning(f"[明日方舟猜干员] 语音检索失败：{cnname}，将在下次更新时重试")
                continue
            root = etree.HTML(data)
            voice_data = root.xpath('//div[@id="voice-data-root"]').pop()
            voice_base = voice_data.xpath("@data-voice-base").pop()
            for language in voice_base.split(","):
                language, voice_path = language.split(":")
                if language not in DATA[cnname]:
                    logger.info(f"[明日方舟猜干员] 新增语音：{cnname}-{language}，正在下载")
                    name = "阿米娅" if cnname == "阿米娅(近卫)" else cnname
                    try:
                        resp = await client.get(
                            f"https://static.prts.wiki/{voice_path}/{name}_标题.wav"
                        )
                        if resp.status_code != 200:
                            logger.warning(
                                f"[明日方舟猜干员] 语音下载失败：{cnname}-{language}，将在下次更新时重试"
                            )
                            continue
                        voice = resp.content
                    except httpx.ReadTimeout:
                        logger.warning(
                            f"[明日方舟猜干员] 语音下载失败：{cnname}-{language}，将在下次更新时重试"
                        )
                        continue
                    voice_silk = await async_decode(voice)
                    DATAPATH.joinpath(f"{cnname}_{language}.silk").write_bytes(
                        voice_silk
                    )
                    DATA[cnname].append(language)
                    logger.info(f"[明日方舟猜干员] 语音下载完成：{cnname}-{language}")
            await asyncio.sleep(0.3)
    logger.info("[明日方舟猜干员] 数据更新完成")
    DATAFILE.write_text(json.dumps(DATA, ensure_ascii=False, indent=4))


def get_voice():
    char = random.choice(list(DATA.keys()))
    language = random.choice(DATA[char])
    voice = DATAPATH.joinpath(f"{char}_{language}.silk").read_bytes()
    return char, voice
