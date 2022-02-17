import re
import json
import asyncio

from pathlib import Path
from loguru import logger
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group
from graia.ariadne.exception import UnknownTarget
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, Plain
from graia.scheduler.timers import every_custom_seconds
from graia.scheduler.saya.schema import SchedulerSchema
from graia.ariadne.event.lifecycle import ApplicationLaunched
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.mirai import BotLeaveEventKick, BotLeaveEventActive
from graia.ariadne.message.parser.twilight import Twilight, FullMatch, WildcardMatch

from config import yaml_data
from util.text2image import create_image
from util.control import Permission, Interval

from .dynamic_shot import get_dynamic_screenshot
from util.sendMessage import safeSendGroupMessage
from .bilibili_request import dynamic_svr, get_status_info_by_uids

saya = Saya.current()
channel = Channel.current()

if yaml_data["Saya"]["BilibiliDynamic"]["EnabledProxy"]:
    if yaml_data["Saya"]["BilibiliDynamic"]["Intervals"] < 30:
        logger.error("动态更新间隔时间过短（不得低于30秒），请重新设置")
        exit()
    else:
        TIME_INTERVALS = 1
else:
    if yaml_data["Saya"]["BilibiliDynamic"]["Intervals"] < 200:
        logger.error("由于你未使用代理，动态更新间隔时间过短（不得低于200秒），请重新设置")
        exit()
    else:
        TIME_INTERVALS = 30

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
    num = 0
    for subuid in dynamic_list["subscription"]:
        if groupid in dynamic_list["subscription"][subuid]:
            num += 1
    return num


def get_group_sublist(groupid):
    sublist = []
    for subuid in dynamic_list["subscription"]:
        if groupid in dynamic_list["subscription"][subuid]:
            sublist.append(subuid)
    return sublist


def get_subid_list():
    """获取所有的订阅"""
    subid_list = []
    for subid in dynamic_list["subscription"]:
        subid_list.append(subid)
    return subid_list


async def add_uid(uid, groupid):

    pattern = re.compile("^[0-9]*$|com/([0-9]*)")
    match = pattern.search(uid)
    if match:
        if match.group(1):
            uid = match.group(1)
        else:
            uid = match.group(0)
    else:
        return Plain("请输入正确的 UP UID 或 首页链接")

    r = await dynamic_svr(uid)
    if "cards" in r["data"]:
        up_name = r["data"]["cards"][0]["desc"]["user_profile"]["info"]["uname"]
        uid_sub_group = dynamic_list["subscription"].get(uid, [])
        if groupid in uid_sub_group:
            return Plain(f"本群已订阅UP {up_name}（{uid}）")
        else:
            if uid not in dynamic_list["subscription"]:
                LIVE_STATUS[uid] = False
                dynamic_list["subscription"][uid] = []
                last_dynid = r["data"]["cards"][0]["desc"]["dynamic_id"]
                DYNAMIC_OFFSET[uid] = last_dynid
            if get_group_sub(groupid) == 12:
                return Plain("每个群聊最多仅可订阅 12 个 UP")
            dynamic_list["subscription"][uid].append(groupid)
            with dynamic_list_json.open("w", encoding="utf-8") as f:
                json.dump(dynamic_list, f, indent=2)
            return Plain(f"成功在本群订阅UP {up_name}（{uid}）")
    else:
        return Plain(f"该UP（{uid}）未发布任何动态，订阅失败")


def remove_uid(uid, groupid):

    pattern = re.compile("^[0-9]*$|com/([0-9]*)")
    match = pattern.search(uid)
    if match:
        if match.group(1):
            uid = match.group(1)
        else:
            uid = match.group(0)
    else:
        return Plain("请输入正确的 UP UID 或 首页链接")

    uid_sub_group = dynamic_list["subscription"].get(uid, [])
    if groupid in uid_sub_group:
        dynamic_list["subscription"][uid].remove(groupid)
        if dynamic_list["subscription"][uid] == []:
            del dynamic_list["subscription"][uid]
        with open(
            "./saya/BilibiliDynamic/dynamic_list.json", "w", encoding="utf-8"
        ) as f:
            json.dump(dynamic_list, f, indent=2)
        return Plain(f"退订成功（{uid}）")
    else:
        return Plain(f"本群未订阅该UP（{uid}）")


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
        logger.info("[BiliBili推送] 由于未订阅任何账号，本次初始化结束")
        return
    await asyncio.sleep(1)
    logger.info(f"[BiliBili推送] 将对 {sub_num} 个账号进行监控")
    info_msg = [f"[BiliBili推送] 将对 {sub_num} 个账号进行监控"]
    data = {"uids": subid_list}
    r = await get_status_info_by_uids(data)
    for uid_statu in r["data"]:
        if r["data"][uid_statu]["live_status"] == 1:
            LIVE_STATUS[uid_statu] = True
        else:
            LIVE_STATUS[uid_statu] = False

    i = 1
    for up_id in subid_list:
        res = await dynamic_svr(up_id)
        if not res:
            logger.error("[BiliBili推送] 寄！")
            return
        if "cards" in res["data"]:
            last_dynid = res["data"]["cards"][0]["desc"]["dynamic_id"]
            DYNAMIC_OFFSET[up_id] = last_dynid
            up_name = res["data"]["cards"][0]["desc"]["user_profile"]["info"]["uname"]
            if len(str(i)) == 1:
                si = f"  {i}"
            elif len(str(i)) == 2:
                si = f" {i}"
            else:
                si = i
            if LIVE_STATUS.get(up_id, False):
                live_status = " > 已开播"
            else:
                live_status = ""
            info_msg.append(f"    ● {si}  ---->  {up_name}({up_id}){live_status}")
            logger.info(
                f"[BiliBili推送] 正在初始化  ● {si}  ---->  {up_name}({up_id}){live_status}"
            )
            i += 1
        else:
            delete_uid(up_id)
        await asyncio.sleep(TIME_INTERVALS)

    NONE = True
    await asyncio.sleep(1)

    if i - 1 != sub_num:
        info_msg.append(f"[BiliBili推送] 共有 {sub_num-i+1} 个账号无法获取最近动态，暂不可进行监控，已从列表中移除")
    for msg in info_msg:
        logger.info(msg)

    image = await create_image("\n".join(info_msg), 100)
    await app.sendFriendMessage(
        yaml_data["Basic"]["Permission"]["Master"],
        MessageChain.create([Image(data_bytes=image)]),
    )


@channel.use(
    SchedulerSchema(
        every_custom_seconds(yaml_data["Saya"]["BilibiliDynamic"]["Intervals"])
    )
)
async def update_scheduled(app: Ariadne):

    if yaml_data["Saya"]["BilibiliDynamic"]["Disabled"]:
        return

    if not NONE:
        logger.info("[BiliBili推送] 初始化未完成，终止本次更新")
        return
    elif len(dynamic_list["subscription"]) == 0:
        logger.info("[BiliBili推送] 由于未订阅任何账号，本次更新已终止")
        return

    sub_list = dynamic_list["subscription"].copy()
    subid_list = get_subid_list()
    post_data = {"uids": subid_list}
    logger.info("[BiliBili推送] 正在检测直播更新")
    live_statu = await get_status_info_by_uids(post_data)
    logger.info("[BiliBili推送] 直播更新成功")
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
            if LIVE_STATUS[up_id]:
                continue
            else:
                LIVE_STATUS[up_id] = True
                logger.info(f"[BiliBili推送] {up_name} 开播了 - {room_area} - {title}")
                for groupid in sub_list[up_id]:
                    try:
                        await app.sendGroupMessage(
                            groupid,
                            MessageChain.create(
                                Plain(
                                    f"本群订阅的UP {up_name}（{up_id}）在 {room_area} 开播啦 ！\n"
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
                            f"[BiliBili推送] 推送失败，找不到该群 {groupid}，已删除该群订阅的 {len(remove_list)} 个UP"
                        )
        else:
            if LIVE_STATUS[up_id]:
                LIVE_STATUS[up_id] = False
                logger.info(f"[BiliBili推送] {up_name} 已下播")
                try:
                    for groupid in sub_list[up_id]:
                        await app.sendGroupMessage(
                            groupid,
                            MessageChain.create(f"本群订阅的UP {up_name}（{up_id}）已下播！"),
                        )
                        await asyncio.sleep(1)
                except UnknownTarget:
                    remove_list = []
                    for subid in get_group_sublist(groupid):
                        remove_uid(subid, groupid)
                        remove_list.append(subid)
                    logger.info(
                        f"[BiliBili推送] 推送失败，找不到该群 {groupid}，已删除该群订阅的 {len(remove_list)} 个UP"
                    )

    logger.info("[BiliBili推送] 正在检测动态更新")
    for up_id in sub_list:
        r = await dynamic_svr(up_id)
        if r:
            if "cards" in r["data"]:
                up_name = r["data"]["cards"][0]["desc"]["user_profile"]["info"]["uname"]
                up_last_dynid = r["data"]["cards"][0]["desc"]["dynamic_id"]
                logger.debug(f"[BiliBili推送] {up_name}（{up_id}）检测完成")
                if up_last_dynid > DYNAMIC_OFFSET[up_id]:
                    logger.info(f"[BiliBili推送] {up_name} 更新了动态 {up_last_dynid}")
                    DYNAMIC_OFFSET[up_id] = up_last_dynid
                    dyn_url_str = r["data"]["cards"][0]["desc"]["dynamic_id_str"]
                    shot_image = await get_dynamic_screenshot(
                        r["data"]["cards"][0]["desc"]["dynamic_id_str"]
                    )
                    for groupid in sub_list[up_id]:
                        try:
                            await app.sendGroupMessage(
                                groupid,
                                MessageChain.create(
                                    [
                                        Plain(f"本群订阅的UP {up_name}（{up_id}）更新动态啦！"),
                                        Image(data_bytes=shot_image),
                                        Plain(f"https://t.bilibili.com/{dyn_url_str}"),
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
                                f"[BiliBili推送] 推送失败，找不到该群 {groupid}，已删除该群订阅的 {len(remove_list)} 个UP"
                            )
                        except Exception as e:
                            logger.info(f"[BiliBili推送] 推送失败，未知错误 {type(e)}")
                await asyncio.sleep(TIME_INTERVALS)
            else:
                delete_uid(up_id)
                logger.info(f"{up_id} 暂时无法监控，已从列表中移除")
                await app.sendFriendMessage(
                    yaml_data["Basic"]["Permission"]["Master"],
                    MessageChain.create([Plain(f"{up_id} 暂时无法监控，已从列表中移除")]),
                )
        else:
            await app.sendFriendMessage(
                yaml_data["Basic"]["Permission"]["Master"],
                MessageChain.create([Plain("动态更新失败超过 3 次，已终止本次更新")]),
            )
            break

    logger.info("[BiliBili推送] 本轮检测完成")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                {"head": FullMatch("订阅"), "anything": WildcardMatch(optional=True)}
            )
        ],
        decorators=[Permission.require(Permission.GROUP_ADMIN), Interval.require()],
    )
)
async def add_sub(group: Group, anything: WildcardMatch):

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
            Twilight(
                {"head": FullMatch("退订"), "anything": WildcardMatch(optional=True)}
            )
        ],
        decorators=[Permission.require(Permission.GROUP_ADMIN), Interval.require()],
    )
)
async def remove_sub(group: Group, anything: WildcardMatch):

    if anything.matched:
        await safeSendGroupMessage(
            group,
            MessageChain.create([remove_uid(anything.result.asDisplay(), group.id)]),
        )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight({"head": FullMatch("本群订阅列表")})],
        decorators=[Permission.require(Permission.GROUP_ADMIN), Interval.require()],
    )
)
async def sub_list(group: Group):

    sublist = []
    for subid in get_group_sublist(group.id):
        sublist.append(subid)
    sublist_count = len(sublist)
    if sublist_count == 0:
        await safeSendGroupMessage(group, MessageChain.create([Plain("本群未订阅任何 UP")]))
    else:
        await safeSendGroupMessage(
            group,
            MessageChain.create(
                [Plain(f"本群共订阅 {sublist_count} 个 UP\n"), Plain("\n".join(sublist))]
            ),
        )


@channel.use(ListenerSchema(listening_events=[BotLeaveEventActive, BotLeaveEventKick]))
async def bot_leave(group: Group):
    remove_list = []
    for subid in get_group_sublist(group.id):
        remove_uid(subid, group.id)
        remove_list.append(subid)
    logger.info(
        f"[BiliBili推送] 检测到退群事件 > {group.name}({group.id})，已删除该群订阅的 {len(remove_list)} 个UP"
    )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight({"head": FullMatch("查看动态"), "anything": WildcardMatch()})
        ],
        decorators=[Permission.require(), Interval.require(20)],
    )
)
async def vive_dyn(group: Group, anything: WildcardMatch):

    if anything.matched:
        pattern = re.compile("^[0-9]*$|com/([0-9]*)")
        match = pattern.search(anything.result.asDisplay())
        if match:
            if match.group(1):
                uid = match.group(1)
            else:
                uid = match.group(0)
        else:
            return await safeSendGroupMessage(
                group, MessageChain.create([Plain("请输入正确的 UP UID 或 首页链接")])
            )

        res = await dynamic_svr(uid)
        if "cards" in res["data"]:
            shot_image = await get_dynamic_screenshot(
                res["data"]["cards"][0]["desc"]["dynamic_id_str"]
            )
            await safeSendGroupMessage(
                group, MessageChain.create([Image(data_bytes=shot_image)])
            )
        else:
            await safeSendGroupMessage(
                group, MessageChain.create([Plain("该UP未发布任何动态")])
            )
