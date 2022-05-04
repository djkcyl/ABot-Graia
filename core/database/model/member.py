import time as t

from pydantic import BaseModel
from beanie import Document, Indexed


class Answers(BaseModel):
    english: int = 0
    arknights: int = 0


class Ban(BaseModel):
    status: bool = False
    operator: int = None
    unban_time: int = None
    group: int = None
    reason: str = None


class Sign(BaseModel):
    is_sign: bool = False
    total_days: int = 0
    continuous_days: int = 0


class Coin(BaseModel):
    total_num: int = 0


class LastTalk(BaseModel):
    time: int = 0
    event: int = None


class MemberTalk(BaseModel):
    total_num: int = 0
    last_talk: LastTalk = None


class ABotMemberData(Document):
    uid: int
    qid: Indexed(int, unique=True)
    join_time: int = int(t.time())
    talk: MemberTalk = MemberTalk()
    coin: Coin = Coin()
    sign: Sign = Sign()
    ban: Ban = Ban()
    answers: Answers = Answers()
