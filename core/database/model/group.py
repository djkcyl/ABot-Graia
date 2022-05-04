import time as t

from pydantic import BaseModel
from beanie import Document, Indexed
from graia.ariadne.message.chain import MessageChain


class Functions(BaseModel):
    disabled: list[str] = []
    data: dict = {}


class Whitelist(BaseModel):
    status: bool = False
    time: int = int(t.time())
    operator: int = None


class Blacklist(BaseModel):
    status: bool = False
    time: int = int(t.time())
    operator: int = None
    reason: str = None


class WBList(BaseModel):
    whitelist: Whitelist
    blacklist: Blacklist


class LastTalk(BaseModel):
    time: int = 0
    member: int = None
    message_chain: MessageChain = None


class GroupTalk(BaseModel):
    total_num: int = 0
    last_talk: LastTalk


class ABotGroupData(Document):
    uid: int
    gid: Indexed(int, unique=True)
    talk: GroupTalk
    join_time: int = int(t.time())
    inviter: int = None
    wblist: WBList
    functions: Functions
