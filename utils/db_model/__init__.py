from datetime import datetime
from typing import Literal
from zoneinfo import ZoneInfo

from beanie import Document
from pymongo import IndexModel


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


class CoinLog(Document):
    qid: str
    group_id: str | None
    coin: int
    source: str
    detail: str = ""
    time: datetime = datetime.now(ZoneInfo("Asia/Shanghai"))

    class Settings:
        name = "core_log_coin"
        indexes = [IndexModel("qid")]


class BanLog(Document):
    target_id: str
    target_type: Literal["user", "group"]
    action: Literal["ban", "unban"]
    ban_time: datetime = datetime.now(ZoneInfo("Asia/Shanghai"))
    ban_reason: str | None = None
    ban_source: str | None = None

    class Settings:
        name = "core_log_ban"


class GroupData(Document):
    group_id: str
    disable_functions: list[str] = []
    banned: bool = False

    class Settings:
        name = "core_group"
        indexes = [IndexModel("group_id", unique=True)]
