import json
import torch
import hanlp
import httpx
import asyncio

from io import BytesIO
from pathlib import Path
from loguru import logger
from zoneinfo import ZoneInfo
from datetime import datetime
from graia.saya import Channel
from PIL import Image as PILImage
from graia.ariadne.app import Ariadne
from miniopy_async.error import S3Error
from graia.ariadne.event import MiraiEvent
from graia.scheduler.timers import every_hour
from graia.scheduler.saya.schema import SchedulerSchema
from hanlp.pretrained.tok import COARSE_ELECTRA_SMALL_ZH
from aiohttp.client_exceptions import ClientResponseError
from graia.ariadne.event.lifecycle import ApplicationLaunched
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.message import GroupMessage, ActiveMessage
from graia.ariadne.message.element import Plain, MultimediaElement, Image
from hanlp.components.tokenizers.transformer import TransformerTaggingTokenizer

from util.ocr import ocr_core
from core_bak.s3file import WeedFS
from util.sougou_scel import SogouScel
from core_bak.function import build_metadata
from core_bak.model import FuncType, AUserModel
from core_bak.db_model import EventLog, GroupMessageLog, ImageOCRLog


channel = Channel.current()
channel.meta = build_metadata(
    func_type=FuncType.system,
    name="事件记录",
    version="1.0",
    description="记录 Bot 所有事件",
    can_be_disabled=False,
    hidden=True,
)

TOK: TransformerTaggingTokenizer
HOTWORD_URL = "https://pinyin.sogou.com/d/dict/download_cell.php"
HOTWORD_PARAMS = {"id": 4, "name": "网络热词", "f": "detail"}
HOTWORD_FILE_PATH = Path("data", "hotword.json")
BAK_FILE_PATH = Path("data", "hotword.json.bak")


@channel.use(ListenerSchema(listening_events=[MiraiEvent]))
async def main(app: Ariadne, event: MiraiEvent):
    if isinstance(event, ActiveMessage):
        return
    if isinstance(event, GroupMessage):
        auser = await AUserModel.init(user=str(event.sender.id))
        await auser.add_talk()
        massage = event.message_chain
        if new_message := massage.include(Plain).display.strip():
            tokenizer: list[str] = await asyncio.to_thread(TOK, new_message, tasks="tok/coarse")
            await GroupMessageLog(
                message_chain=list(massage.__root__),
                qid=str(event.sender.id),
                group_id=str(event.sender.group.id),
                message_tokenizer=" ".join(tokenizer),
            ).insert()  # type: ignore
        else:
            await GroupMessageLog(
                message_chain=list(massage.__root__),
                qid=str(event.sender.id),
                group_id=str(event.sender.group.id),
            ).insert()  # type: ignore
        if media := massage.include(MultimediaElement):
            for i in media.get(MultimediaElement):
                weed = app.launch_manager.get_interface(WeedFS)
                try:
                    object_exist = await weed.get_object(
                        "abot", i.id, app.service.client_session
                    )
                except S3Error as e:
                    if e.code == "NoSuchKey":
                        object_exist = None
                    else:
                        raise e
                if object_exist:
                    continue

                await updae_file(i, weed)

    else:
        await EventLog(**event.dict()).insert()  # type: ignore


async def updae_file(i: MultimediaElement, weed: WeedFS):
    for _ in range(3):
        try:
            data = await i.get_bytes()
            await weed.put_object("abot", i.id, BytesIO(data), len(data))
            logger.info(f"[Func.event_log] 上传文件 {i.id} 到 Weed")
            if isinstance(i, Image):
                ocr_result = await asyncio.to_thread(ocr_core.ocr, PILImage.open(BytesIO(data)))
                ocr_text = " ".join([x["text"] for x in ocr_result]).strip()
                await ImageOCRLog(
                    image_id=i.id or datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%d%H%M%S%f"),
                    ocr_result=[
                        {
                            "text": x["text"],
                            "score": x["score"],
                            "position": x["position"].tolist(),
                        }
                        for x in ocr_result
                    ],
                    ocr_text=" ".join(
                        await asyncio.to_thread(TOK, ocr_text, tasks="tok/coarse")
                    )
                    if ocr_text
                    else None,
                ).insert()  # type: ignore
                if ocr_text:
                    print_text = f"{ocr_text[:20]}..." if len(ocr_text) > 20 else ocr_text
                    logger.info(f"[Func.event_log] 识别文件 {i.id} 文字：{print_text}")
            break

        except ClientResponseError as e:
            if e.status != 404:
                logger.warning(f"[Func.event_log] 无法获取文件 {i.id}，{e.message}，尝试重试")
                continue
            else:
                logger.warning(f"[Func.event_log] 无法获取文件 {i.id}，{e.message}，跳过")
                break
    else:
        logger.error(f"[Func.event_log] 无法获取文件 {i.id}，已重试 3 次，跳过")


@channel.use(SchedulerSchema(every_hour()))
@channel.use(ListenerSchema(listening_events=[ApplicationLaunched], priority=10))
async def init_update():
    global TOK
    logger.info("[Task.event_log] 正在下载更新搜狗网络热词词库")

    async with httpx.AsyncClient() as client:
        for _ in range(3):
            try:
                resp = await client.get(HOTWORD_URL, params=HOTWORD_PARAMS)
                resp.raise_for_status()
                break
            except httpx.HTTPError as e:
                logger.warning(f"[Task.event_log] 词库下载失败: {e}")
                continue
        else:
            logger.error("[Task.event_log] 词库下载失败，已重试 3 次，跳过")
            exit(1)

    hotword = SogouScel.parse(resp.content)
    hotword_set: set[str] = {x.word for x in hotword}

    if HOTWORD_FILE_PATH.exists():
        try:
            with HOTWORD_FILE_PATH.open("r", encoding="utf-8") as file:
                hotword_data: set[str] = set(json.load(file))
        except json.JSONDecodeError:
            logger.error("[Task.event_log] 词库文件解析失败，跳过")
            hotword_data = set()
    else:
        hotword_data = set()

    new_word = hotword_set - hotword_data
    hotword_data |= hotword_set

    try:
        with BAK_FILE_PATH.open("w", encoding="utf-8") as file:
            json.dump(list(hotword_data), file, ensure_ascii=False)
    except Exception as e:
        logger.error(f"[Task.event_log] 写入词库文件失败: {e}")
        return
    try:
        BAK_FILE_PATH.rename(HOTWORD_FILE_PATH)
    except Exception as e:
        logger.error(f"[Task.event_log] 重命名词库文件失败: {e}，已恢复备份文件")
        return

    logger.success(f"[Task.event_log] 成功更新 {len(new_word)} 个热词")

    if not locals().get("TOK"):
        logger.info("[Task.event_log] 正在加载 HanLP 分词模型")
        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        TOK = hanlp.load(COARSE_ELECTRA_SMALL_ZH, devices=device)
    TOK.dict_force = hotword_data
