import re
import json
import asyncio

from pathlib import Path
from loguru import logger
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group
from graia.ariadne.exception import UnknownTarget
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Plain
from graia.scheduler.saya.schema import SchedulerSchema
from graia.scheduler.timers import every_custom_seconds
from graia.ariadne.event.lifecycle import ApplicationLaunched
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.mirai import BotLeaveEventActive, BotLeaveEventKick
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    RegexResult,
    WildcardMatch,
)

from config import yaml_data
from util.text2image import create_image
from util.sendMessage import safeSendGroupMessage
from util.control import Function, Interval, Permission

from .grpc.req import grpc_dyn_get
from .dynamic_shot import get_dynamic_screenshot
from .bilibili_request import get_status_info_by_uids

channel = Channel.current()

HOME = Path(__file__).parent
DYNAMIC_OFFSET = {}
LIVE_STATUS = {}
NONE = False

head = {
    "user-agent": (
        "Mozilla/5.0 (Windows NT 6.1) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/41.0.2228.0 "
        "Safari/537.36"
    ),
    "Referer": "https://www.bilibili.com/",
}
dynamic_list_json = HOME.joinpath("dynamic_list.json")
if dynamic_list_json.exists():
    with dynamic_list_json.open("r") as f:
        dynamic_list = json.load(f)
else:
    with dynamic_list_json.open("w") as f:
        dynamic_list = {"subscription": {}}
        json.dump(dynamic_list, f, indent=2)


def get_group_sub(groupid):
    return sum(
        groupid in dynamic_list["subscription"][subuid]
        for subuid in dynamic_list["subscription"]
    )


def get_group_sublist(groupid):
    return [
        subuid
        for subuid in dynamic_list["subscription"]
        if groupid in dynamic_list["subscription"][subuid]
    ]


def get_subid_list():
    """?????????????????????"""
    return list(dynamic_list["subscription"])


async def add_uid(uid, groupid):

    pattern = re.compile("^[0-9]*$|com/([0-9]*)")
    if match := pattern.search(uid):
        uid = match[1] or match[0]
    else:
        return Plain("?????????????????? UP UID ??? ????????????")

    r = await grpc_dyn_get(uid)
    if not r:
        return Plain(f"???UP???{uid}???????????????????????????????????????")
    up_name = r["list"][0]["modules"][0]["module_author"]["author"]["name"]
    uid_sub_group = dynamic_list["subscription"].get(uid, [])
    if groupid in uid_sub_group:
        return Plain(f"???????????????UP {up_name}???{uid}???")
    if uid not in dynamic_list["subscription"]:
        LIVE_STATUS[uid] = False
        dynamic_list["subscription"][uid] = []
        last_dynid = r["list"][0]["extend"]["dyn_id_str"]
        DYNAMIC_OFFSET[uid] = int(last_dynid)
    if get_group_sub(groupid) == 12:
        return Plain("?????????????????????????????? 12 ??? UP")
    dynamic_list["subscription"][uid].append(groupid)
    with dynamic_list_json.open("w", encoding="utf-8") as f:
        json.dump(dynamic_list, f, indent=2)
    return Plain(f"?????????????????????UP {up_name}???{uid}???")


def remove_uid(uid, groupid):

    pattern = re.compile("^[0-9]*$|com/([0-9]*)")
    if match := pattern.search(uid):
        uid = match[1] or match[0]
    else:
        return Plain("?????????????????? UP UID ??? ????????????")

    uid_sub_group = dynamic_list["subscription"].get(uid, [])
    if groupid not in uid_sub_group:
        return Plain(f"??????????????????UP???{uid}???")
    dynamic_list["subscription"][uid].remove(groupid)
    if dynamic_list["subscription"][uid] == []:
        del dynamic_list["subscription"][uid]
    with open("./saya/BilibiliDynamic/dynamic_list.json", "w", encoding="utf-8") as f:
        json.dump(dynamic_list, f, indent=2)
    return Plain(f"???????????????{uid}???")


def delete_uid(uid):
    del dynamic_list["subscription"][uid]
    with open("./saya/BilibiliDynamic/dynamic_list.json", "w", encoding="utf-8") as f:
        json.dump(dynamic_list, f, indent=2)


@channel.use(ListenerSchema(listening_events=[ApplicationLaunched]))
async def init(app: Ariadne):

    global NONE

    if yaml_data["Saya"]["BilibiliDynamic"]["Disabled"]:
        return

    subid_list = get_subid_list()
    sub_num = len(subid_list)
    if sub_num == 0:
        NONE = True
        await asyncio.sleep(1)
        logger.info("[BiliBili??????] ???????????????????????????????????????????????????")
        return
    await asyncio.sleep(1)
    logger.info(f"[BiliBili??????] ?????? {sub_num} ?????????????????????")
    info_msg = [f"[BiliBili??????] ?????? {sub_num} ?????????????????????"]
    data = {"uids": subid_list}
    r = await get_status_info_by_uids(data)
    for uid_statu in r["data"]:
        LIVE_STATUS[uid_statu] = r["data"][uid_statu]["live_status"] == 1
    i = 1
    for up_id in subid_list:
        res = await grpc_dyn_get(up_id)
        if not res:
            logger.error("[BiliBili??????] ??????")
            return
        last_dynid = res["list"][0]["extend"]["dyn_id_str"]
        DYNAMIC_OFFSET[up_id] = int(last_dynid)
        up_name = res["list"][0]["modules"][0]["module_author"]["author"]["name"]
        if len(str(i)) == 1:
            si = f"  {i}"
        elif len(str(i)) == 2:
            si = f" {i}"
        else:
            si = i
        live_status = " > ?????????" if LIVE_STATUS.get(up_id, False) else ""
        info_msg.append(f"    ??? {si}  ---->  {up_name}({up_id}){live_status}")
        logger.info(f"[BiliBili??????] ???????????????  ??? {si}  ---->  {up_name}({up_id}){live_status}")
        i += 1
        await asyncio.sleep(1)

    NONE = True
    await asyncio.sleep(1)

    if i - 1 != sub_num:
        info_msg.append(f"[BiliBili??????] ?????? {sub_num-i+1} ?????????????????????????????????????????????????????????????????????????????????")
    for msg in info_msg:
        logger.info(msg)

    image = await create_image("\n".join(info_msg), 100)
    await app.sendFriendMessage(
        yaml_data["Basic"]["Permission"]["Master"],
        MessageChain.create([Image(data_bytes=image)]),
    )


@channel.use(SchedulerSchema(every_custom_seconds(3)))
async def update_scheduled(app: Ariadne):

    if yaml_data["Saya"]["BilibiliDynamic"]["Disabled"]:
        return

    if not NONE:
        logger.info("[BiliBili??????] ???????????????????????????????????????")
        return
    elif len(dynamic_list["subscription"]) == 0:
        logger.info("[BiliBili??????] ???????????????????????????????????????????????????")
        return

    sub_list = dynamic_list["subscription"].copy()
    subid_list = get_subid_list()
    post_data = {"uids": subid_list}
    logger.info("[BiliBili??????] ????????????????????????")
    live_statu = await get_status_info_by_uids(post_data)
    logger.info("[BiliBili??????] ??????????????????")
    for up_id in live_statu["data"]:
        title = live_statu["data"][up_id]["title"]
        room_id = live_statu["data"][up_id]["room_id"]
        room_area = (
            live_statu["data"][up_id]["area_v2_parent_name"]
            + " / "
            + live_statu["data"][up_id]["area_v2_name"]
        )
        up_name = live_statu["data"][up_id]["uname"]
        cover_from_user = live_statu["data"][up_id]["cover_from_user"]

        if live_statu["data"][up_id]["live_status"] == 1:
            if up_id not in LIVE_STATUS:
                LIVE_STATUS[up_id] = False
            if not LIVE_STATUS[up_id]:
                LIVE_STATUS[up_id] = True
                logger.info(f"[BiliBili??????] {up_name} ????????? - {room_area} - {title}")
                for groupid in sub_list[up_id]:
                    try:
                        await app.sendGroupMessage(
                            groupid,
                            MessageChain.create(
                                Plain(
                                    f"???????????????UP {up_name}???{up_id}?????? {room_area} ???????????? ???\n"
                                ),
                                Plain(title),
                                Image(url=cover_from_user),
                                Plain(f"\nhttps://live.bilibili.com/{room_id}"),
                            ),
                        )
                        await asyncio.sleep(1)
                    except UnknownTarget:
                        remove_list = []
                        for subid in get_group_sublist(groupid):
                            remove_uid(subid, groupid)
                            remove_list.append(subid)
                        logger.info(
                            f"[BiliBili??????] ?????????????????????????????? {groupid}??????????????????????????? {len(remove_list)} ???UP"
                        )
        elif LIVE_STATUS[up_id]:
            LIVE_STATUS[up_id] = False
            logger.info(f"[BiliBili??????] {up_name} ?????????")
            try:
                for groupid in sub_list[up_id]:
                    await app.sendGroupMessage(
                        groupid,
                        MessageChain.create(f"???????????????UP {up_name}???{up_id}???????????????"),
                    )
                    await asyncio.sleep(1)
            except UnknownTarget:
                remove_list = []
                for subid in get_group_sublist(groupid):
                    remove_uid(subid, groupid)
                    remove_list.append(subid)
                logger.info(
                    f"[BiliBili??????] ?????????????????????????????? {groupid}??????????????????????????? {len(remove_list)} ???UP"
                )

    logger.info("[BiliBili??????] ????????????????????????")
    for up_id in sub_list:
        r = await grpc_dyn_get(up_id)
        if r:
            up_name = r["list"][0]["modules"][0]["module_author"]["author"]["name"]
            up_last_dynid = r["list"][0]["extend"]["dyn_id_str"]
            logger.debug(f"[BiliBili??????] {up_name}???{up_id}???????????????")
            if int(up_last_dynid) > DYNAMIC_OFFSET[up_id]:
                logger.info(f"[BiliBili??????] {up_name} ??????????????? {up_last_dynid}")
                shot_image = await get_dynamic_screenshot(up_last_dynid)
                if shot_image:
                    for groupid in sub_list[up_id]:
                        try:
                            await app.sendGroupMessage(
                                groupid,
                                MessageChain.create(
                                    [
                                        Plain(f"???????????????UP {up_name}???{up_id}?????????????????????"),
                                        Image(data_bytes=shot_image),
                                        Plain(f"https://t.bilibili.com/{up_last_dynid}"),
                                    ]
                                ),
                            )
                            await asyncio.sleep(1)
                        except UnknownTarget:
                            remove_list = []
                            for subid in get_group_sublist(groupid):
                                remove_uid(subid, groupid)
                                remove_list.append(subid)
                            logger.info(
                                f"[BiliBili??????] ?????????????????????????????? {groupid}??????????????????????????? {len(remove_list)} ???UP"
                            )
                        except Exception as e:
                            logger.info(f"[BiliBili??????] ??????????????????????????? {type(e)}")
                    DYNAMIC_OFFSET[up_id] = int(up_last_dynid)
                else:
                    logger.error(f"[BiliBili??????] {up_name} ?????????????????? 3 ?????????????????????????????????????????????")
            await asyncio.sleep(1)
        else:
            await app.sendFriendMessage(
                yaml_data["Basic"]["Permission"]["Master"],
                MessageChain.create([Plain("???????????????????????? 3 ???????????????????????????")]),
            )
            break

    logger.info("[BiliBili??????] ??????????????????")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([FullMatch("??????"), "anything" @ WildcardMatch(optional=True)])
        ],
        decorators=[
            Permission.require(Permission.GROUP_ADMIN),
            Function.require("BilibiliDynamic"),
            Interval.require(),
        ],
    )
)
async def add_sub(group: Group, anything: RegexResult):

    if anything.matched:
        add = await add_uid(anything.result.asDisplay(), group.id)
        await safeSendGroupMessage(
            group,
            MessageChain.create(add),
        )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([FullMatch("??????"), "anything" @ WildcardMatch(optional=True)])
        ],
        decorators=[
            Permission.require(Permission.GROUP_ADMIN),
            Function.require("BilibiliDynamic"),
            Interval.require(),
        ],
    )
)
async def remove_sub(group: Group, anything: RegexResult):

    if anything.matched:
        await safeSendGroupMessage(
            group,
            MessageChain.create([remove_uid(anything.result.asDisplay(), group.id)]),
        )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(FullMatch("??????????????????"))],
        decorators=[Permission.require(Permission.GROUP_ADMIN), Interval.require()],
    )
)
async def sub_list(group: Group):

    sublist = list(get_group_sublist(group.id))
    sublist_count = len(sublist)
    if sublist_count == 0:
        await safeSendGroupMessage(group, MessageChain.create([Plain("????????????????????? UP")]))
    else:
        await safeSendGroupMessage(
            group,
            MessageChain.create(
                [Plain(f"??????????????? {sublist_count} ??? UP\n"), Plain("\n".join(sublist))]
            ),
        )


@channel.use(ListenerSchema(listening_events=[BotLeaveEventActive, BotLeaveEventKick]))
async def bot_leave(group: Group):
    remove_list = []
    for subid in get_group_sublist(group.id):
        remove_uid(subid, group.id)
        remove_list.append(subid)
    logger.info(
        f"[BiliBili??????] ????????????????????? > {group.name}({group.id})??????????????????????????? {len(remove_list)} ???UP"
    )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("????????????"), "anything" @ WildcardMatch()])],
        decorators=[Permission.require(), Interval.require(20)],
    )
)
async def vive_dyn(group: Group, anything: RegexResult):

    if not anything.matched:
        return
    pattern = re.compile("^[0-9]*$|com/([0-9]*)")
    if match := pattern.search(anything.result.asDisplay()):
        uid = match[1] or match[0]
    else:
        return await safeSendGroupMessage(
            group, MessageChain.create([Plain("?????????????????? UP UID ??? ????????????")])
        )

    res = await grpc_dyn_get(uid)
    if res:
        shot_image = await get_dynamic_screenshot(res["list"][0]["extend"]["dyn_id_str"])
        await safeSendGroupMessage(
            group, MessageChain.create([Image(data_bytes=shot_image)])
        )
    else:
        await safeSendGroupMessage(group, MessageChain.create([Plain("???UP?????????????????????")]))
