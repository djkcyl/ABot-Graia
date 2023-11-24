from beanie import Document
from zoneinfo import ZoneInfo
from datetime import datetime
from pymongo import IndexModel, TEXT
from typing import Optional, Literal
from graia.ariadne.event import MiraiEvent
from graia.ariadne.message.element import Element


class AUser(Document):
    uid: int
    qid: str
    coin: int = 10
    is_sign: bool = False
    is_chat: bool = False
    today_transferred: int = 0
    total_sign: int = 0
    totle_talk: int = 0
    continue_sign: int = 0
    banned: bool = False
    join_time: datetime = datetime.now(ZoneInfo("Asia/Shanghai"))

    class Settings:
        name = "core_user"
        indexes = [IndexModel("uid", unique=True), IndexModel("qid", unique=True)]


class SignLog(Document):
    qid: str
    group_id: str
    sign_time: datetime = datetime.now(ZoneInfo("Asia/Shanghai"))

    class Settings:
        name = "core_log_sign"
        indexes = [IndexModel("qid")]


class EventLog(MiraiEvent, Document):
    log_time: datetime = datetime.now(ZoneInfo("Asia/Shanghai"))

    class Settings:
        name = "core_log_event"


class GroupMessageLog(Document):
    message_chain: list[Element]
    qid: str
    group_id: str
    log_time: datetime = datetime.now(ZoneInfo("Asia/Shanghai"))

    message_tokenizer: Optional[str]

    class Settings:
        name = "core_log_group_message"
        indexes = [IndexModel([("message_tokenizer", TEXT)])]


class CoinLog(Document):
    qid: str
    group_id: Optional[str]
    coin: int
    source: str
    detail: str = ""
    time: datetime = datetime.now(ZoneInfo("Asia/Shanghai"))

    class Settings:
        name = "core_log_coin"
        indexes = [IndexModel("qid")]


class GroupData(Document):
    group_id: str
    disable_functions: list[str] = []
    banned: bool = False

    class Settings:
        name = "core_group"
        indexes = [IndexModel("group_id", unique=True)]


class BanLog(Document):
    target_id: str
    target_type: Literal["user", "group"]
    action: Literal["ban", "unban"]
    ban_time: datetime = datetime.now(ZoneInfo("Asia/Shanghai"))
    ban_reason: Optional[str] = None
    ban_source: Optional[str] = None

    class Settings:
        name = "core_log_ban"


class FunctionLog(Document):
    qid: str
    group_id: Optional[str]
    function: str
    action: Literal["enable", "disable", "call", "call_fail"]
    time: datetime = datetime.now(ZoneInfo("Asia/Shanghai"))

    class Settings:
        name = "core_log_function"
        indexes = [IndexModel("qid"), IndexModel("group_id"), IndexModel("function")]


class ImageOCRLog(Document):
    image_id: str
    ocr_result: list[dict[str, str | float | list[list[int]]]]
    ocr_text: Optional[str]

    class Settings:
        name = "core_log_image_ocr"
        indexes = [IndexModel("image_id", unique=True), IndexModel([("ocr_text", TEXT)])]
