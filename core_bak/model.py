from loguru import logger
from enum import Enum, auto
from typing import Optional
from pydantic import BaseModel
from graia.ariadne.model import Member, Group

from .db_model import AUser, SignLog, CoinLog, GroupData, BanLog


class AUserModel(AUser, BaseModel):
    @classmethod
    async def init(cls, user: AUser | str | int | Member):
        if isinstance(user, str | int):
            user_id = str(user)
        elif isinstance(user, Member):
            user_id = str(user.id)
        elif not isinstance(user, AUser):
            raise TypeError(f"无法识别的用户类型：{type(user)}")
        else:
            user_id = user.qid
        if not isinstance(user, AUser):
            user = await AUser.find_one(AUser.qid == user_id)  # type: ignore
            if not user:
                last_userid = await AUser.find_one(sort=[("_id", -1)])
                uid = int(last_userid.uid) + 1 if last_userid else 1
                await AUser(uid=uid, qid=user_id).insert()  # type: ignore
                user = await AUser.find_one(AUser.qid == user_id)  # type: ignore
                logger.info(f"[Core.db] 已初始化用户：{user_id}")

        return cls(**user.dict())

    async def ban(self, reason: str, source: str):
        if self.banned:
            return False
        self.banned = True
        await self.save()  # type: ignore
        await BanLog(
            target_id=self.qid,
            target_type="user",
            action="ban",
            ban_reason=reason,
            ban_source=source,
        ).insert()  # type: ignore
        return True

    async def unban(self, reason: str, source: str):
        if not self.banned:
            return False
        self.banned = False
        await self.save()  # type: ignore
        await BanLog(
            target_id=self.qid,
            target_type="user",
            action="unban",
            ban_reason=reason,
            ban_source=source,
        ).insert()  # type: ignore
        return True

    async def sign(self, group_id: str | int):
        if self.is_sign:
            return False
        self.is_sign = True
        self.total_sign += 1
        self.continue_sign += 1
        await self.save()  # type: ignore
        await SignLog(qid=self.qid, group_id=str(group_id)).insert()  # type: ignore
        return True

    async def add_coin(
        self,
        num: int,
        group_id: Optional[str | int] = None,
        source: str = "未知",
        detail: str = "",
    ):
        self.coin += num
        await self.save()  # type: ignore
        await CoinLog(qid=self.qid, group_id=str(group_id), coin=num, source=source, detail=detail).insert()  # type: ignore

    async def reduce_coin(
        self,
        num: int,
        force: bool = False,
        group_id: Optional[str | int] = None,
        source: str = "未知",
        detail: str = "",
    ):
        if self.coin < num:
            if not force:
                return False
            now_coin = self.coin
            self.coin = 0
            await self.save()  # type: ignore
            await CoinLog(
                qid=self.qid,
                group_id=str(group_id),
                coin=-now_coin,
                source=source,
                detail=detail,
            ).insert()  # type: ignore
            return now_coin
        else:
            self.coin -= num
            await self.save()  # type: ignore
            await CoinLog(
                qid=self.qid,
                group_id=str(group_id),
                coin=-num,
                source=source,
                detail=detail,
            ).insert()  # type: ignore
            return True

    async def add_talk(self):
        self.totle_talk += 1
        self.is_chat = True
        await self.save()  # type: ignore


class AGroupModel(GroupData, BaseModel):
    @classmethod
    async def init(cls, group: GroupData | Group | str | int):
        if isinstance(group, str | int):
            group_id = str(group)
        elif isinstance(group, Group):
            group_id = str(group.id)
        elif not isinstance(group, GroupData):
            raise TypeError(f"无法识别的群组类型：{type(group)}")
        else:
            group_id = group.group_id
        if not isinstance(group, GroupData):
            group = await GroupData.find_one(GroupData.group_id == group_id)  # type: ignore
            if not group:
                await GroupData(group_id=group_id).insert()  # type: ignore
                group = await GroupData.find_one(GroupData.group_id == group_id)  # type: ignore
                logger.info(f"[Core.db] 已初始化群：{group_id}")  # type: ignore

        return cls(**group.dict())

    async def ban(self, reason: str, source: str):
        if self.banned:
            return False
        self.banned = True
        await self.save()  # type: ignore
        await BanLog(
            target_id=self.group_id,
            target_type="group",
            action="ban",
            ban_reason=reason,
            ban_source=source,
        ).insert()  # type: ignore
        return True

    async def unban(self, reason: str, source: str):
        if not self.banned:
            return False
        self.banned = False
        await self.save()  # type: ignore
        await BanLog(
            target_id=self.group_id,
            target_type="group",
            action="unban",
            ban_reason=reason,
            ban_source=source,
        ).insert()  # type: ignore
        return True

    async def disable_function(self, function: str, meta: "FuncItem"):
        if function in self.disable_functions or not meta.can_be_disabled:
            return False
        self.disable_functions.append(function)
        await self.save()  # type: ignore
        return True

    async def enable_function(self, function: str, meta: "FuncItem"):
        if function not in self.disable_functions or meta.maintain:
            return False
        self.disable_functions.remove(function)
        await self.save()  # type: ignore
        return True


class FuncType(str, Enum):
    system = "核心"
    user = "用户"
    tool = "工具"
    fun = "娱乐"
    push = "推送"
    admin = "管理"


class FuncItem(BaseModel):
    func_type: FuncType
    name: str
    version: str
    description: str
    usage: list[str]
    options: list[dict[str, str]]
    example: list[dict[str, str]]
    can_be_disabled: bool
    default_enable: bool
    hidden: bool
    maintain: bool


class DataSource(Enum):
    SELF = auto()
    GROUP = auto()
    GLOBAL = auto()


class TimeRange(Enum):
    DAY = auto()
    WEEK = auto()
    MONTH = auto()
    YEAR = auto()
