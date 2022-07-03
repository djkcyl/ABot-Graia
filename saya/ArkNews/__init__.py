import json
import time
import httpx
import random
import asyncio

from pathlib import Path
from loguru import logger
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import UploadMethod
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Plain
from graia.scheduler.saya.schema import SchedulerSchema
from graia.scheduler.timers import every_custom_seconds
from graia.ariadne.event.lifecycle import ApplicationLaunched
from graia.saya.builtins.broadcast.schema import ListenerSchema

from util.TimeTool import TimeRecorder
from config import group_data, yaml_data
from util.text2image import create_image

from .get_news import Game, WeiboUser

channel = Channel.current()
game = Game()

HOME = Path(__file__).parent
WEIBO_LOCK = False
GAME_LOCK = False
PUSHED_LIST_FILE = HOME.joinpath("pushed_list.json")
if PUSHED_LIST_FILE.exists():
    with PUSHED_LIST_FILE.open("r") as f:
        pushed_list = json.load(f)
else:
    with PUSHED_LIST_FILE.open("w") as f:
        pushed_list = {"weibo": {}, "game": None, "last_time": int(time.time())}
        json.dump(pushed_list, f, indent=2)


def save_pushed_list():
    with PUSHED_LIST_FILE.open("w") as f:
        json.dump(pushed_list, f, indent=2)


def last_time():

    global pushed_list

    now_time = int(time.time())
    last_time = pushed_list.get("last_time", now_time)
    if (now_time - last_time) > 3600:
        logger.info("[明日方舟蹲饼] 与上次间隔过长，重新计算")
        pushed_list = {"weibo": {}, "game": None, "last_time": now_time}
        resp = True
    else:
        resp = False
    pushed_list["last_time"] = now_time
    save_pushed_list()
    return resp


@channel.use(SchedulerSchema(every_custom_seconds(60)))
@channel.use(ListenerSchema(listening_events=[ApplicationLaunched]))
async def get_weibo_news(app: Ariadne):

    global WEIBO_LOCK

    # 总开关
    if yaml_data["Saya"]["ArkNews"]["Disabled"]:
        return

    if WEIBO_LOCK or last_time():
        return
    else:
        WEIBO_LOCK = True

    # 遍历需要推送的微博 id 表
    for weibo_id in yaml_data["Saya"]["ArkNews"]["WeiboUserList"]:
        # 实例化微博用户
        weibo = WeiboUser(weibo_id)
        pushed = pushed_list["weibo"]
        weibo_id = str(weibo_id)
        if weibo_id not in pushed:
            pushed[weibo_id] = []
        new_id = await weibo.get_weibo_id(0)

        # 如果获取失败，则跳过
        if not new_id:
            continue

        # 如果获取到的 id 与之前的 id 相同或者为空，则跳过
        if not pushed[weibo_id]:
            pushed_list["weibo"][weibo_id].append(new_id)
            save_pushed_list()
            await asyncio.sleep(1)
            logger.info(f"[明日方舟蹲饼] {weibo_id} 微博初始化成功，当前最新微博：{new_id}")
            continue
        elif not isinstance(new_id, str) or new_id in pushed[weibo_id]:
            continue

        # 进入推送流程
        # 获取最新微博正文内容
        result = await weibo.get_weibo_content(0)
        if not result:
            await app.sendFriendMessage(
                yaml_data["Basic"]["Permission"]["Master"],
                MessageChain.create(f"微博推送失败，USER：{weibo_id}，ID：{new_id}，终止本次流程"),
            )
            continue

        # 开始计时并推送
        time_rec = TimeRecorder()

        group_list = (
            [await app.getGroup(yaml_data["Basic"]["Permission"]["DebugGroup"])]
            if yaml_data["Basic"]["Permission"]["Debug"]
            else [
                x
                for x in await app.getGroupList()
                if "ArkNews" not in group_data[str(x.id)]["DisabledFunc"]
            ]
        )

        group_count = len(group_list)
        logger.info(f"[明日方舟蹲饼] {result.user_name} 微博已更新：{new_id}，共需推送 {group_count} 个群")

        # 构建消息链
        msg = [
            Plain(f"{result.user_name} 更新了新的微博 {new_id}\n"),
            Plain(f"{result.detail_url}\n"),
            await app.uploadImage(
                await create_image(result.html_text, 72), UploadMethod.Group
            ),
        ] + [
            await app.uploadImage(x, UploadMethod.Group)(x, UploadMethod.Group)
            for x in result.pics_list
        ]

        await app.sendFriendMessage(
            yaml_data["Basic"]["Permission"]["Master"], MessageChain.create(msg)
        )
        for group in group_list:
            await app.sendMessage(group, MessageChain.create(msg))
            await asyncio.sleep(random.uniform(2, 4))

        await app.sendFriendMessage(
            yaml_data["Basic"]["Permission"]["Master"],
            MessageChain.create(
                f"{result.user_name} 的微博 {new_id} 推送结束，耗时{time_rec.total()}"
            ),
        ),

        # 存储获取到的 id 至已推送列表
        pushed_list["weibo"][weibo_id].append(new_id)
        save_pushed_list()

        await asyncio.sleep(5)

    WEIBO_LOCK = False


@channel.use(SchedulerSchema(every_custom_seconds(30)))
@channel.use(ListenerSchema(listening_events=[ApplicationLaunched]))
async def get_game_news(app: Ariadne):

    global GAME_LOCK

    if yaml_data["Saya"]["ArkNews"]["Disabled"]:
        return

    if GAME_LOCK or last_time():
        return
    else:
        GAME_LOCK = True

    pushed = pushed_list["game"] or []
    try:
        latest_list = await game.get_announce()
    except httpx.HTTPError:
        logger.error("[明日方舟蹲饼] 获取游戏公告失败")
        return
    new_list = list(set(latest_list) - set(pushed))

    if not pushed:
        pushed_list["game"] = latest_list
        save_pushed_list()
        await asyncio.sleep(1)
        logger.info(f"[明日方舟蹲饼] 游戏公告初始化成功，当前共有 {len(latest_list)} 条公告")
        return
    elif not new_list:
        return

    pushed_list["game"] = latest_list
    save_pushed_list()

    group_list = (
        [await app.getGroup(yaml_data["Basic"]["Permission"]["DebugGroup"])]
        if yaml_data["Basic"]["Permission"]["Debug"]
        else [
            x
            for x in await app.getGroupList()
            if "ArkNews" not in group_data[str(x.id)]["DisabledFunc"]
        ]
    )

    for announce in new_list:
        time_rec = TimeRecorder()
        logger.info(f"[明日方舟蹲饼] 游戏公告已更新：{announce}")
        image = await game.get_screenshot(announce)
        msg = [Plain("明日方舟更新了新的游戏公告\n"), Image(data_bytes=image)]

        await app.sendFriendMessage(
            yaml_data["Basic"]["Permission"]["Master"], MessageChain.create(msg)
        )
        for group in group_list:
            await app.sendMessage(group, MessageChain.create(msg))
            await asyncio.sleep(random.uniform(2, 4))

        await app.sendFriendMessage(
            yaml_data["Basic"]["Permission"]["Master"],
            MessageChain.create([Plain(f"游戏公告推送结束，耗时{time_rec.total()}")]),
        )

        await asyncio.sleep(3)

    GAME_LOCK = False
