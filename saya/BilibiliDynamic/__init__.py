import os
import json
import httpx
import asyncio

from graia.saya import Saya, Channel
from graia.broadcast.interrupt.waiter import Waiter
from graia.application import GraiaMiraiApplication
from graia.broadcast.interrupt import InterruptControl
from graia.scheduler.timers import every_custom_seconds
from graia.scheduler.saya.schema import SchedulerSchema
from graia.application.event.messages import GroupMessage
from graia.application.group import Group, Member, MemberPerm
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.event.lifecycle import ApplicationLaunched
from graia.application.message.parser.literature import Literature
from graia.application.message.elements.internal import MessageChain, Plain, Image_UnsafeBytes

from config import yaml_data, group_data
from util.limit import group_limit_check
from util.UserBlock import black_list_block

from .dynamic_shot import get_dynamic_screenshot

saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
inc = InterruptControl(bcc)

OFFSET = {}

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


async def add_uid(uid, groupid):
    async with httpx.AsyncClient() as client:
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
                OFFSET[uid] = last_dynid
            if get_group_sub(groupid) == 8:
                return Plain(f"每个群聊最多仅可订阅 8 个 UP")
            dynamic_list['subscription'][uid].append(groupid)
            with open('./saya/BilibiliDynamic/dynamic_list.json', 'w', encoding="utf-8") as f:
                json.dump(dynamic_list, f, indent=2)
            return Plain(f"成功在本群订阅 {up_name}（{uid}）")
    else:
        Plain(f"该UP（{uid}）未发布任何动态，订阅失败")


async def remove_uid(uid, groupid):
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
    sub_num = len(dynamic_list["subscription"])
    info_msg = [f"[BiliBili推送] 将对 {sub_num} 个账号进行监控"]
    i = 1
    for up_id in dynamic_list["subscription"]:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/space_history?host_uid={up_id}")
            r = r.json()
        if "cards" in r["data"]:
            last_dynid = r["data"]["cards"][0]["desc"]["dynamic_id"]
            OFFSET[up_id] = last_dynid
            up_name = r["data"]["cards"][0]["desc"]["user_profile"]["info"]["uname"]
            if len(str(i)) == 1:
                si = f"  {i}"
            elif len(str(i)) == 2:
                si = f" {i}"
            else:
                si = i
            sub_count = len(dynamic_list["subscription"][up_id])
            info_msg.append(f"  ● {si}  ---->  {up_name}({up_id}) > {sub_count} > {last_dynid}")
            i += 1
        else:
            delete_uid(up_id)
        await asyncio.sleep(1)
    await asyncio.sleep(1)
    if i-1 != sub_num:
        info_msg.append(f"[BiliBili推送] 共有 {sub_num-i+1} 个账号无法获取信息，暂不可进行监控，已从列表中移除")
    for msg in info_msg:
        app.logger.info(msg)


def get_sub_dict():
    return dynamic_list["subscription"]


@channel.use(SchedulerSchema(every_custom_seconds(yaml_data['Saya']['BilibiliDynamic']['Intervals'])))
async def update_scheduled(app: GraiaMiraiApplication):

    if yaml_data['Saya']['BilibiliDynamic']['Disabled']:
        return

    app.logger.info("[BiliBili推送] 正在检测动态更新")
    sub_list = get_sub_dict()
    for up_id in sub_list:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/space_history?host_uid={up_id}")
            r = r.json()
        if "cards" in r["data"]:
            up_name = r["data"]["cards"][0]["desc"]["user_profile"]["info"]["uname"]
            up_last_dynid = r["data"]["cards"][0]["desc"]["dynamic_id"]
            app.logger.info(f"[BiliBili推送] 正在检测{up_name}（{up_id}）")
            if up_last_dynid > OFFSET[up_id]:
                app.logger.info(f"   > 更新了动态 {up_last_dynid}")
                OFFSET[up_id] = up_last_dynid
                shot_image = await get_dynamic_screenshot(r["data"]["cards"][0]["desc"]["dynamic_id_str"])
                for groupid in sub_list[up_id]:
                    await app.sendGroupMessage(groupid, MessageChain.create([
                        Plain(f"本群订阅的UP {up_name}（{up_id}）更新啦！"),
                        Image_UnsafeBytes(shot_image)
                    ]))
                    await asyncio.sleep(0.3)
        else:
            delete_uid(up_id)
            app.logger.info(f"{up_id} 暂时无法监控，已从列表中移除")
        await asyncio.sleep(5)


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
            await app.sendGroupMessage(group, MessageChain.create([await remove_uid(saying[1], group.id)]))
    else:
        await app.sendGroupMessage(group, MessageChain.create([
            Plain("你没有权限使用该功能！")
        ]))
