import os
import json
import httpx
import asyncio

from graia.saya import Saya, Channel
from graia.application import GraiaMiraiApplication
from graia.scheduler.timers import every_custom_seconds
from graia.scheduler.saya.schema import SchedulerSchema
from graia.application.event.messages import FriendMessage, GroupMessage
from graia.application.group import Group, Member, MemberPerm
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.event.lifecycle import ApplicationLaunched
from graia.application.message.parser.literature import Literature
from graia.application.message.elements.internal import MessageChain, Plain, Image_UnsafeBytes
from graia.application.event.mirai import BotLeaveEventKick, BotLeaveEventActive

from config import yaml_data
from util.GetProxy import get_proxy
from util.text2image import create_image
from util.limit import group_limit_check
from util.UserBlock import black_list_block

from .dynamic_shot import get_dynamic_screenshot

saya = Saya.current()
channel = Channel.current()

DYNAMIC_OFFSET = {}
LIVE_STATUS = {}
NONE = False

head = {
    'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
    'Referer': 'https://www.bilibili.com/'
}

if os.path.exists('./saya/BilibiliDynamic/dynamic_list.json'):
    with open('./saya/BilibiliDynamic/dynamic_list.json', 'r', encoding="utf-8") as f:
        dynamic_list = json.load(f)
else:
    with open('./saya/BilibiliDynamic/dynamic_list.json', 'w', encoding="utf-8") as f:
        dynamic_list = {
            "subscription": {}
        }
        json.dump(dynamic_list, f, indent=2)


def get_group_sub(groupid):
    num = 0
    for subuid in dynamic_list['subscription']:
        if groupid in dynamic_list['subscription'][subuid]:
            num += 1
    return num


def get_group_sublist(groupid):
    sublist = []
    for subuid in dynamic_list['subscription']:
        if groupid in dynamic_list['subscription'][subuid]:
            sublist.append(subuid)
    return sublist


def get_subid_list():
    subid_list = []
    for subid in dynamic_list['subscription']:
        subid_list.append(subid)
    return subid_list


async def add_uid(uid, groupid):
    async with httpx.AsyncClient(proxies=get_proxy(), headers=head) as client:
        r = await client.get(f"https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/space_history?host_uid={uid}")
        r = r.json()
    if "cards" in r["data"]:
        up_name = r["data"]["cards"][0]["desc"]["user_profile"]["info"]["uname"]
        uid_sub_group = dynamic_list['subscription'].get(uid, [])
        if groupid in uid_sub_group:
            return Plain(f"本群已订阅 {up_name}（{uid}）")
        else:
            if uid not in dynamic_list['subscription']:
                dynamic_list['subscription'][uid] = []
                last_dynid = r["data"]["cards"][0]["desc"]["dynamic_id"]
                DYNAMIC_OFFSET[uid] = last_dynid
            if get_group_sub(groupid) == 8:
                return Plain(f"每个群聊最多仅可订阅 8 个 UP")
            dynamic_list['subscription'][uid].append(groupid)
            with open('./saya/BilibiliDynamic/dynamic_list.json', 'w', encoding="utf-8") as f:
                json.dump(dynamic_list, f, indent=2)
            return Plain(f"成功在本群订阅 {up_name}（{uid}）")
    else:
        Plain(f"该UP（{uid}）未发布任何动态，订阅失败")


def remove_uid(uid, groupid):
    uid_sub_group = dynamic_list['subscription'].get(uid, [])
    if groupid in uid_sub_group:
        dynamic_list['subscription'][uid].remove(groupid)
        if dynamic_list['subscription'][uid] == []:
            del dynamic_list['subscription'][uid]
        with open('./saya/BilibiliDynamic/dynamic_list.json', 'w', encoding="utf-8") as f:
            json.dump(dynamic_list, f, indent=2)
        return Plain(f"退订成功（{uid}）")
    else:
        return Plain(f"本群未订阅该UP（{uid}）")


def delete_uid(uid):
    del dynamic_list['subscription'][uid]
    with open('./saya/BilibiliDynamic/dynamic_list.json', 'w', encoding="utf-8") as f:
        json.dump(dynamic_list, f, indent=2)


@channel.use(ListenerSchema(listening_events=[ApplicationLaunched]))
async def init(app: GraiaMiraiApplication):

    global NONE

    if yaml_data['Saya']['BilibiliDynamic']['Disabled']:
        return

    subid_list = get_subid_list()
    sub_num = len(subid_list)
    if sub_num == 0:
        NONE = True
        return app.logger.info(f"[BiliBili推送] 由于未订阅任何账号，本次初始化结束")
    info_msg = [f"[BiliBili推送] 将对 {sub_num} 个账号进行监控"]

    data = {"uids": subid_list}
    async with httpx.AsyncClient(proxies=get_proxy(), headers=head) as client:
        r = await client.post("https://api.live.bilibili.com/room/v1/Room/get_status_info_by_uids", json=data)
        r = r.json()
    for uid_statu in r["data"]:
        if r["data"][uid_statu]["live_status"] == 1:
            LIVE_STATUS[uid_statu] = True
        else:
            LIVE_STATUS[uid_statu] = False

    i = 1
    for up_id in subid_list:
        for ri in range(5):
            try:
                async with httpx.AsyncClient(proxies=get_proxy(), headers=head) as client:
                    r = await client.get(f"https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/space_history?host_uid={up_id}")
                    res = r.json()
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
                        live_status = "已开播"
                    else:
                        live_status = "未开播"
                    sub_count = len(dynamic_list["subscription"][up_id])
                    info_msg.append(f"    ● {si}  ---->  {up_name}({up_id}) > 当前{live_status}")
                    info_msg.append(f"                       最新动态：{last_dynid}")
                    info_msg.append(f"                       共有 {sub_count} 个群订阅了该 UP")
                    for groupid in dynamic_list["subscription"][up_id]:
                        group_info = await app.getGroup(groupid)
                        info_msg.append(f"                           > {group_info.name}({groupid})")
                    i += 1
                    await asyncio.sleep(1)
                else:
                    delete_uid(up_id)
            except:
                app.logger.error(f"{up_id} 更新失败，正在第 {ri + 1} 重试")
                pass
            else:
                if r.status_code == 200:
                    break
        else:
            return
    NONE = True
    await asyncio.sleep(1)
    if i-1 != sub_num:
        info_msg.append(f"[BiliBili推送] 共有 {sub_num-i+1} 个账号无法获取信息，暂不可进行监控，已从列表中移除")
    for msg in info_msg:
        app.logger.info(msg)

    image = await create_image("\n".join(info_msg), 100)
    await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
        Image_UnsafeBytes(image.getvalue())
    ]))


@channel.use(SchedulerSchema(every_custom_seconds(yaml_data['Saya']['BilibiliDynamic']['Intervals'])))
async def update_scheduled(app: GraiaMiraiApplication):

    if yaml_data['Saya']['BilibiliDynamic']['Disabled']:
        return

    if not NONE:
        return app.logger.info("[BiliBili推送] 初始化未完成，终止本次更新")
    elif len(dynamic_list["subscription"]) == 0:
        return app.logger.info(f"[BiliBili推送] 由于未订阅任何账号，本次更新已终止")

    sub_list = dynamic_list["subscription"].copy()
    subid_list = get_subid_list()
    post_data = {"uids": subid_list}
    app.logger.info("[BiliBili推送] 正在检测直播更新")
    for retry in range(3):
        try:
            async with httpx.AsyncClient(proxies=get_proxy(), headers=head) as client:
                r = await client.post(f"https://api.live.bilibili.com/room/v1/Room/get_status_info_by_uids", json=post_data)
                live_statu = r.json()
                if r.status_code == 200:
                    break
        except httpx.HTTPError as e:
            app.logger.error(f"[BiliBili推送] 直播更新失败，正在重试")
            app.logger.error(f"{str(type(e))}\n{str(e.request)}\n{str(e)}")
        except Exception as e:
            app.logger.error(f"[BiliBili推送] 直播更新失败，正在重试")
            app.logger.error(f"{str(type(e))}\n{str(e)}")
            image = await create_image(f"{str(type(e))}\n{str(e)}", 120)
            await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
                Plain(f"BiliBili 直播检测失败 {retry + 1} 次\n"),
                Image_UnsafeBytes(image.getvalue())
            ]))
    else:
        app.logger.error(f"[BiliBili推送] 直播更新失败超过 {retry + 1} 次，已终止本次更新")
        return await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
            Plain(f"BiliBili 直播检测失败超过 {retry + 1} 次，已终止本次检测")
        ]))

    for up_id in live_statu["data"]:
        title = live_statu["data"][up_id]["title"]
        room_id = live_statu["data"][up_id]["room_id"]
        room_area = live_statu["data"][up_id]["area_v2_parent_name"] + " / " + live_statu["data"][up_id]["area_v2_name"]
        up_name = live_statu["data"][up_id]["uname"]

        if live_statu["data"][up_id]["live_status"] == 1:
            if LIVE_STATUS[up_id]:
                continue
            else:
                LIVE_STATUS[up_id] = True
                app.logger.info(f"[BiliBili推送] {up_name} 开播了 - {room_area} - {title}")
                for groupid in sub_list[up_id]:
                    await app.sendGroupMessage(groupid, MessageChain.create([
                        Plain(f"本群订阅的UP {up_name}（{up_id}）在 {room_area} 开播啦 ！\n"),
                        Plain(title),
                        Plain(f"\nhttps://live.bilibili.com/{room_id}")
                    ]))
                    await asyncio.sleep(0.3)
        else:
            if LIVE_STATUS[up_id]:
                app.logger.info(f"[BiliBili推送] {up_name} 已下播")
                LIVE_STATUS[up_id] = False

    app.logger.info("[BiliBili推送] 正在检测动态更新")
    for up_id in sub_list:
        for retry in range(3):
            try:
                async with httpx.AsyncClient(proxies=get_proxy(), headers=head) as client:
                    r = await client.get(f"https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/space_history?host_uid={up_id}")
                    if r.status_code == 200:
                        break
            except httpx.HTTPError as e:
                app.logger.error(f"[BiliBili推送] 动态更新失败，正在重试")
                app.logger.error(f"{str(type(e))}\n{str(e.request)}\n{str(e)}")
            except Exception as e:
                app.logger.error(f"[BiliBili推送] 动态更新失败，正在重试")
                app.logger.error(f"{str(type(e))}\n{str(e)}")
                image = await create_image(f"{str(type(e))}\n{str(e)}", 120)
                await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
                    Plain(f"BiliBili 动态检测失败 {retry + 1} 次\n"),
                    Image_UnsafeBytes(image.getvalue())
                ]))
        else:
            app.logger.error(f"[BiliBili推送] 动态更新失败超过 {retry + 1} 次，已终止本次更新")
            await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
                Plain(f"BiliBili 动态检测失败超过 {retry + 1} 次，已终止本次检测")
            ]))
            break
        r = r.json()
        if "cards" in r["data"]:
            up_name = r["data"]["cards"][0]["desc"]["user_profile"]["info"]["uname"]
            up_last_dynid = r["data"]["cards"][0]["desc"]["dynamic_id"]
            app.logger.debug(f"[BiliBili推送] 正在检测{up_name}（{up_id}）")
            if up_last_dynid > DYNAMIC_OFFSET[up_id]:
                app.logger.info(f"[BiliBili推送] {up_name} 更新了动态 {up_last_dynid}")
                DYNAMIC_OFFSET[up_id] = up_last_dynid
                shot_image = await get_dynamic_screenshot(r["data"]["cards"][0]["desc"]["dynamic_id_str"])
                for groupid in sub_list[up_id]:
                    await app.sendGroupMessage(groupid, MessageChain.create([
                        Plain(f"本群订阅的UP {up_name}（{up_id}）更新动态啦！"),
                        Image_UnsafeBytes(shot_image)
                    ]))
                    await asyncio.sleep(0.3)
            await asyncio.sleep(1)
        else:
            delete_uid(up_id)
            app.logger.info(f"{up_id} 暂时无法监控，已从列表中移除")
            await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
                Plain(f"{up_id} 暂时无法监控，已从列表中移除")
            ]))
    app.logger.info("[BiliBili推送] 本轮检测完成")


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Literature("订阅")],
                            headless_decorators=[group_limit_check(10), black_list_block()]))
async def atrep(app: GraiaMiraiApplication, group: Group, member: Member, message: MessageChain):

    if member.permission in [MemberPerm.Administrator, MemberPerm.Owner] or member.id in yaml_data['Basic']['Permission']['Admin']:
        saying = message.asDisplay().split(" ", 1)
        if len(saying) == 2:
            await app.sendGroupMessage(group, MessageChain.create([await add_uid(saying[1], group.id)]))
    else:
        await app.sendGroupMessage(group, MessageChain.create([
            Plain("你没有权限使用该功能！")
        ]))


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Literature("退订")],
                            headless_decorators=[group_limit_check(10), black_list_block()]))
async def atrep(app: GraiaMiraiApplication, group: Group, member: Member, message: MessageChain):

    if member.permission in [MemberPerm.Administrator, MemberPerm.Owner] or member.id in yaml_data['Basic']['Permission']['Admin']:
        saying = message.asDisplay().split(" ", 1)
        if len(saying) == 2:
            await app.sendGroupMessage(group, MessageChain.create([remove_uid(saying[1], group.id)]))
    else:
        await app.sendGroupMessage(group, MessageChain.create([
            Plain("你没有权限使用该功能！")
        ]))


@channel.use(ListenerSchema(listening_events=[BotLeaveEventActive, BotLeaveEventKick]))
async def bot_leave(app: GraiaMiraiApplication, group: Group):
    remove_list = []
    for subid in get_group_sublist(group.id):
        remove_uid(subid, group.id)
        remove_list.append(subid)
    app.logger.info(f"[BiliBili推送] 检测到退群事件 > {group.name}({group.id})，已删除该群订阅的 {len(remove_list)} 个UP")
