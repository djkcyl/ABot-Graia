import json
import random
import asyncio

from pathlib import Path
from loguru import logger
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Image
from graia.scheduler.timers import every_custom_seconds
from graia.scheduler.saya.schema import SchedulerSchema
from graia.ariadne.event.lifecycle import ApplicationLaunched
from graia.saya.builtins.broadcast.schema import ListenerSchema

from util.TimeTool import TimeRecorder
from config import yaml_data, group_data
from util.text2image import create_image
from util.sendMessage import selfSendGroupMessage

from .get_news import Weibo, Game

saya = Saya.current()
channel = Channel.current()
weibo = Weibo()
game = Game()

HOME = Path(__file__).parent
PUSHED_LIST_FILE = HOME.joinpath("pushed_list.json")
if PUSHED_LIST_FILE.exists():
    with PUSHED_LIST_FILE.open("r") as f:
        pushed_list = json.load(f)
else:
    with PUSHED_LIST_FILE.open("w") as f:
        pushed_list = {
            "weibo": None,
            "game": None
        }
        json.dump(pushed_list, f, indent=2)


def save_pushed_list():
    with PUSHED_LIST_FILE.open("w") as f:
        json.dump(pushed_list, f, indent=2)


@channel.use(SchedulerSchema(every_custom_seconds(15)))
@channel.use(ListenerSchema(listening_events=[ApplicationLaunched]))
async def get_weibo_news(app: Ariadne):

    if yaml_data['Saya']['ArkNews']['Disabled']:
        return

    try:
        pushed = pushed_list["weibo"]
        new_id = await weibo.requests_content(0, only_id=True)

        if not pushed:
            pushed_list["weibo"] = new_id
            print(pushed_list)
            save_pushed_list()
            await asyncio.sleep(1)
            return logger.info(f"[明日方舟蹲饼] 微博初始化成功，当前最新微博：{new_id}")
        elif not isinstance(new_id, str) or new_id == pushed:
            return False

        pushed_list["weibo"] = new_id
        save_pushed_list()

        group_list = await app.getGroupList()
        result, detail_url, pics_list = await weibo.requests_content(0)

        time_rec = TimeRecorder()
        logger.info(f"[明日方舟蹲饼] 微博已更新：{new_id}")
        image = await create_image(result, 72)
        msg = [
            Plain("明日方舟更新了新的微博\n"),
            Plain(f"{detail_url}\n"),
            Image(data_bytes=image)] + [Image(url=x) for x in pics_list]

        await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create(msg))
        for group in group_list:
            if 'ArkNews' in group_data[str(group.id)]['DisabledFunc']:
                continue
            await selfSendGroupMessage(group, MessageChain.create(msg))
            await asyncio.sleep(random.randint(3, 5))

        await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
            Plain(f'微博推送结束，耗时{time_rec.total()}')
        ]))

    except IndexError:
        pass


@channel.use(SchedulerSchema(every_custom_seconds(30)))
@channel.use(ListenerSchema(listening_events=[ApplicationLaunched]))
async def get_game_news(app: Ariadne):

    if yaml_data['Saya']['ArkNews']['Disabled']:
        return

    pushed = pushed_list["game"] if pushed_list["game"] else []
    latest_list = await game.get_announce()
    new_list = list(set(latest_list) - set(pushed))

    # print(len(pushed))
    # print(len(latest_list))
    # print(len(new_list))

    if not pushed:
        pushed_list["game"] = latest_list
        save_pushed_list()
        await asyncio.sleep(1)
        return logger.info(f"[明日方舟蹲饼] 游戏公告初始化成功，当前共有 {len(latest_list)} 条公告")
    elif not new_list:
        return

    pushed_list["game"] = latest_list
    save_pushed_list()

    group_list = await app.getGroupList()

    for announce in new_list:
        time_rec = TimeRecorder()
        logger.info(f"[明日方舟蹲饼] 游戏公告已更新：{announce}")
        image = await game.get_screenshot(announce)
        msg = [
            Plain("明日方舟更新了新的游戏公告\n"),
            Image(data_bytes=image)
        ]

        await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create(msg))
        for group in group_list:
            if 'ArkNews' in group_data[str(group.id)]['DisabledFunc']:
                continue
            await selfSendGroupMessage(group, MessageChain.create(msg))
            await asyncio.sleep(random.randint(3, 5))

        await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
            Plain(f'游戏公告推送结束，耗时{time_rec.total()}')
        ]))

        await asyncio.sleep(3)
