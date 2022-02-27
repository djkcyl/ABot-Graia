from enum import Enum
from typing import List
from pydantic import BaseModel


class DynamicType(str, Enum):
    dyn_none = 0
    forward = 1
    av = 2
    pgc = 3
    courses = 4
    fold = 5
    word = 6
    draw = 7
    article = 8
    music = 9
    common_square = 10
    common_vertical = 11
    live = 12
    medialist = 13
    courses_season = 14
    ad = 15
    applet = 16
    subscription = 17
    live_rcmd = 18
    banner = 19
    ugc_season = 20
    subscription_new = 21
    story = 22
    topic_rcmd = 23


class Modules(BaseModel):
    pass


class Dynamic(BaseModel):
    card_type: DynamicType
    item_type: DynamicType
    modules: List[Modules]


class DynamicResp(BaseModel):
    DynList: List[Dynamic]
    history_offset: int
    has_more: bool
