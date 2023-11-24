from loguru import logger
from zoneinfo import ZoneInfo
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group
from typing import Optional, Annotated
from datetime import datetime, timedelta
from beanie.odm.enums import SortDirection
from graia.ariadne.message.element import Image
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import Twilight, FullMatch, UnionMatch, ResultValue

from core.db_model import AUser
from core.model import FuncType
from util.text2image import md2img
from core.preprocessor import MentionMe
from core.function import build_metadata
from core.control import Function, Permission, Interval

channel = Channel.current()
channel.meta = build_metadata(
    func_type=FuncType.user,
    name="排行榜",
    version="1.0",
    description="查询 ABot 用户排行榜",
    usage=["发送指令：查看 游戏币/发言/签到 排行榜"],
    options=[{"name": "type", "help": "排行榜类型，可选：游戏币/发言/签到"}],
    can_be_disabled=False,
)

COIN_RANK = (Image(), datetime.now(ZoneInfo("Asia/Shanghai")) - timedelta(days=1))
TALK_RANK = (Image(), datetime.now(ZoneInfo("Asia/Shanghai")) - timedelta(days=1))
SIGN_RANK = (Image(), datetime.now(ZoneInfo("Asia/Shanghai")) - timedelta(days=1))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    FullMatch("查看"),
                    "arg_type" @ UnionMatch("游戏币", "发言", "签到"),
                    FullMatch("排行榜"),
                ],
                preprocessor=MentionMe(),
            ),
        ],
        decorators=[Function.require(), Permission.require(), Interval.require()],
    )
)
async def main(app: Ariadne, group: Group, arg_type: Annotated[MessageChain, ResultValue()]):
    global COIN_RANK, TALK_RANK, SIGN_RANK
    rank_map = {
        "游戏币": COIN_RANK,
        "发言": TALK_RANK,
        "签到": SIGN_RANK,
    }
    rank_image, generate_time = rank_map[arg_type.display]
    if (now_date := datetime.now(ZoneInfo("Asia/Shanghai"))) - generate_time > timedelta(
        minutes=10
    ):
        rank_image = Image(data_bytes=await get_rank(arg_type.display, now_date))
        rank_map[arg_type.display] = (rank_image, now_date)
    await app.send_group_message(group, rank_image)


async def get_rank(rank_type: str, date: datetime, size: Optional[int] = 10):
    app = Ariadne.current()
    date_str = date.strftime("%Y-%m-%d %H:%M:%S")
    rank_str = (
        f"# ABot {rank_type}排行榜\n\n"
        f"当前 ABot 共有 {await AUser.count()} 位用户，更新时间：{date_str}\n\n"
        "| 排名 | 用户ID | 用户QQ | 昵称 | 游戏币 | 发言次数 | 签到天数 |\n"
        "| :-: | :-: | :-: | :-: | :-: | :-: | :-: |\n"
    )
    type_map = {"游戏币": "coin", "发言": "totle_talk", "签到": "total_sign"}
    rank = 1
    async for user in AUser.find_all(
        sort=[(type_map[rank_type], SortDirection.DESCENDING)], limit=size
    ):
        quser = await app.get_user_profile(int(user.qid))
        rank_str += (
            f"| {rank} | {user.uid} | {user.qid} | {quser.nickname} "
            f"| {user.coin} | {user.totle_talk} | {user.total_sign} |\n"
        )
        rank += 1

    logger.info(rank_str)
    return await md2img(rank_str)
