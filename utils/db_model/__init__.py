from datetime import datetime
from typing import Literal
from zoneinfo import ZoneInfo

from beanie import Document
from pymongo import IndexModel


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
