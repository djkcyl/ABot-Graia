# import re
# import json
# import asyncio

# from pathlib import Path
# from loguru import logger
# from graia.saya import Channel
# from graia.ariadne.app import Ariadne
# from graia.ariadne.model import Group
# from graia.ariadne.exception import UnknownTarget
# from graia.ariadne.event.message import GroupMessage
# from graia.ariadne.message.chain import MessageChain
# from graia.ariadne.message.element import Image, Plain
# from graia.scheduler.saya.schema import SchedulerSchema
# from graia.scheduler.timers import every_custom_seconds
# from graia.ariadne.event.lifecycle import ApplicationLaunched
# from graia.saya.builtins.broadcast.schema import ListenerSchema
# from graia.ariadne.event.mirai import BotLeaveEventActive, BotLeaveEventKick
# from graia.ariadne.message.parser.twilight import (
#     Twilight,
#     FullMatch,
#     RegexMatch,
#     RegexResult,
#     WildcardMatch,
# )

# from config import yaml_data
# from util.control import Interval, Permission
# from util.sendMessage import safeSendGroupMessage

# from .dynamic_shot import get_dynamic_screenshot
# from .grpc import grpc_dyn_get, grpc_dynall_get, grpc_uplist_get
# from .grpc.bilibili.app.dynamic.v2.dynamic_pb2 import DynamicType
# from .bilibili_request import bilibili_login, get_status_info_by_uids, relation_modify

# channel = Channel.current()

# HOME = Path(__file__).parent
# LIVEING = []
# OFFSET = ""
# NONE = False

# head = {
#     "user-agent": (
#         "Mozilla/5.0 (Windows NT 6.1) "
#         "AppleWebKit/537.36 (KHTML, like Gecko) "
#         "Chrome/41.0.2228.0 "
#         "Safari/537.36"
#     ),
#     "Referer": "https://www.bilibili.com/",
# }
# dynamic_list_json = HOME.joinpath("dynamic_list.json")
# if dynamic_list_json.exists():
#     with dynamic_list_json.open("r") as f:
#         dynamic_list = json.load(f)
# else:
#     with dynamic_list_json.open("w") as f:
#         dynamic_list = {"subscription": {}}
#         json.dump(dynamic_list, f, indent=2)


# def get_group_sub(groupid):
#     return sum(
#         groupid in dynamic_list["subscription"][subuid]
#         for subuid in dynamic_list["subscription"]
#     )


# def get_group_sublist(groupid):
#     return [
#         subuid
#         for subuid in dynamic_list["subscription"]
#         if groupid in dynamic_list["subscription"][subuid]
#     ]


# def get_subid_list():
#     """获取所有的订阅"""
#     return list(dynamic_list["subscription"])


# async def add_uid(uid, groupid):
#     pattern = re.compile("^[0-9]*$|com/([0-9]*)")
#     if match := pattern.search(uid):
#         uid = match.group(1) or match.group(0)
#     else:
#         return Plain("请输入正确的 UP UID 或 首页链接")

#     r = await grpc_dyn_get(uid)
#     if not r:
#         return Plain(f"该UP（{uid}）未发布任何动态，订阅失败")
#     up_name = r["list"][0]["modules"][0]["module_author"]["author"]["name"]
#     uid_sub_group = dynamic_list["subscription"].get(uid, [])
#     if groupid in uid_sub_group:
#         return Plain(f"本群已订阅UP {up_name}（{uid}）")
#     if get_group_sub(groupid) == 12:
#         return Plain("每个群聊最多仅可订阅 12 个 UP")
#     if uid not in dynamic_list["subscription"]:
#         resp = await relation_modify(uid, 1)
#         if resp["code"] == 0:
#             dynamic_list["subscription"][uid] = []
#         else:
#             return Plain(f"订阅失败 {resp['message']}")
#     dynamic_list["subscription"][uid].append(groupid)
#     with dynamic_list_json.open("w", encoding="utf-8") as f:
#         json.dump(dynamic_list, f, indent=2)
#     return Plain(f"成功在本群订阅UP {up_name}（{uid}）")


# async def remove_uid(uid, groupid):

#     pattern = re.compile("^[0-9]*$|com/([0-9]*)")
#     if match := pattern.search(uid):
#         uid = match.group(1) or match.group(0)
#     else:
#         return Plain("请输入正确的 UP UID 或 首页链接")

#     uid_sub_group = dynamic_list["subscription"].get(uid, [])
#     if groupid not in uid_sub_group:
#         return Plain(f"本群未订阅该UP（{uid}）")
#     dynamic_list["subscription"][uid].remove(groupid)
#     if dynamic_list["subscription"][uid] == []:
#         await delete_uid(uid)
#     with open("./saya/BilibiliDynamic/dynamic_list.json", "w", encoding="utf-8") as f:
#         json.dump(dynamic_list, f, indent=2)
#     return Plain(f"退订成功（{uid}）")


# async def delete_uid(uid):
#     await relation_modify(uid, 2)
#     del dynamic_list["subscription"][uid]
#     with open("./saya/BilibiliDynamic/dynamic_list.json", "w", encoding="utf-8") as f:
#         json.dump(dynamic_list, f, indent=2)


# @channel.use(ListenerSchema(listening_events=[ApplicationLaunched]))
# async def init(app: Ariadne):

#     global NONE, OFFSET

#     if yaml_data["Saya"]["BilibiliDynamic"]["Disabled"]:
#         return

#     await asyncio.sleep(3)
#     await bilibili_login()

#     subid_list = get_subid_list()
#     sub_num = len(subid_list)
#     if sub_num == 0:
#         NONE = True
#         await asyncio.sleep(1)
#         logger.info("[BiliBili推送] 由于未订阅任何账号，本次初始化结束")
#         return
#     await asyncio.sleep(1)
#     logger.info(f"[BiliBili推送] 将对 {sub_num} 个账号进行监控")

#     # 直播状态初始化
#     resp = await grpc_uplist_get()
#     for uid in resp["items"]:
#         if "live_info" in uid:
#             logger.info(f"[BiliBili推送] {uid['name']} 已开播")
#             LIVEING.append(uid["uid"])

#     # 动态初始化
#     resp = await grpc_dynall_get()
#     OFFSET = int(resp[0].extend.dyn_id_str)
#     NONE = True
#     await asyncio.sleep(1)

#     await app.sendFriendMessage(
#         yaml_data["Basic"]["Permission"]["Master"],
#         MessageChain.create(f"[BiliBili推送] 将对 {sub_num} 个账号进行监控"),
#     )


# @channel.use(SchedulerSchema(every_custom_seconds(3)))
# async def update_scheduled(app: Ariadne):
#     global OFFSET

#     if yaml_data["Saya"]["BilibiliDynamic"]["Disabled"]:
#         return

#     if not NONE:
#         logger.info("[BiliBili推送] 初始化未完成，终止本次更新")
#         return
#     elif len(dynamic_list["subscription"]) == 0:
#         return

#     sub_list = dynamic_list["subscription"].copy()

#     # 直播状态更新检测
#     live_statu = await grpc_uplist_get()
#     # 由于叔叔的 api 太烂了，会把同一个 up 开播和未开播的状态放在同一个列表里，所以这里需要去重
#     # 不过好消息是，这个列表可以按照开播和未开播的顺序排列
#     lives = []
#     for up in live_statu["items"]:
#         up_id = up["uid"]
#         up_name = up["name"]
#         # 检测订阅配置里是否有该 up
#         if up_id in sub_list:
#             # 如果已经在被检测过的列表里，则跳过
#             if up_id in lives:
#                 continue
#             else:
#                 lives.append(up_id)
#             # 如果存在直播信息则为已开播
#             if "live_info" in up:
#                 if up_id in LIVEING:
#                     continue
#                 room_id = up["live_info"]["room_id"]
#                 resp = await get_status_info_by_uids({"uids": [up_id]})
#                 room_area = (
#                     resp["data"][up_id]["area_v2_parent_name"]
#                     + " / "
#                     + resp["data"][up_id]["area_v2_name"]
#                 )
#                 cover_from_user = resp["data"][up_id]["cover_from_user"]
#                 title = resp["data"][up_id]["title"]
#                 logger.info(f"[BiliBili推送] {up_name} 开播了 - {room_area} - {title}")

#                 for groupid in sub_list[up_id]:
#                     if (
#                         yaml_data["Basic"]["Permission"]["Debug"]
#                         and groupid != yaml_data["Basic"]["Permission"]["DebugGroup"]
#                     ):
#                         continue
#                     try:
#                         await app.sendGroupMessage(
#                             groupid,
#                             MessageChain.create(
#                                 f"本群订阅的UP {up_name}（{up_id}）在 {room_area} 区开播啦 ！\n{title}\n",
#                                 Image(url=cover_from_user),
#                                 Plain(f"\nhttps://live.bilibili.com/{room_id}"),
#                             ),
#                         )
#                         await asyncio.sleep(1)
#                     except UnknownTarget:
#                         remove_list = []
#                         for subid in get_group_sublist(groupid):
#                             await remove_uid(subid, groupid)
#                             remove_list.append(subid)
#                         logger.info(
#                             f"[BiliBili推送] 推送失败，找不到该群 {groupid}，已删除该群订阅的 {len(remove_list)} 个UP"
#                         )

#                 LIVEING.append(up_id)
#             elif up_id in LIVEING:
#                 LIVEING.remove(up_id)
#                 logger.info(f"[BiliBili推送] {up_name} 已下播")
#                 for groupid in sub_list[up_id]:
#                     if (
#                         yaml_data["Basic"]["Permission"]["Debug"]
#                         and groupid != yaml_data["Basic"]["Permission"]["DebugGroup"]
#                     ):
#                         continue
#                     try:
#                         await app.sendGroupMessage(
#                             groupid,
#                             MessageChain.create(f"本群订阅的UP {up_name}（{up_id}）已下播！"),
#                         )

#                     except UnknownTarget:
#                         remove_list = []
#                         for subid in get_group_sublist(groupid):
#                             await remove_uid(subid, groupid)
#                             remove_list.append(subid)
#                         logger.info(
#                             f"[BiliBili推送] 推送失败，找不到该群 {groupid}，已删除该群订阅的 {len(remove_list)} 个UP"
#                         )
#                     await asyncio.sleep(1)
#         elif yaml_data["Saya"]["BilibiliDynamic"]["AutoUnsubscribe"]:
#             logger.warning(f"[BiliBili推送] 没有找到订阅UP {up_name}（{up_id}）的群，已退订！")
#             resp = await relation_modify(up_id, 2)
#             if resp["code"] == 0:
#                 logger.info("[BiliBili推送] 退订成功！")
#                 await app.sendFriendMessage(
#                     yaml_data["Basic"]["Permission"]["Master"],
#                     MessageChain.create(
#                         f"[BiliBili推送] 未找到订阅 {up_name}（{up_id}）的群，已被退订！",
#                     ),
#                 )

#     # 动态更新检测
#     # 获取当前登录账号的动态列表
#     dynall = await grpc_dynall_get()
#     for dyn in dynall:
#         if int(dyn.extend.dyn_id_str) <= OFFSET:
#             break

#         up_id = str(dyn.modules[0].module_author.author.mid)
#         up_name = dyn.modules[0].module_author.author.name
#         up_last_dynid = dyn.extend.dyn_id_str
#         logger.info(f"[BiliBili推送] {up_name} 更新了动态 {up_last_dynid}")
#         try:
#             shot_image = await get_dynamic_screenshot(up_last_dynid)
#         except Exception as e:
#             logger.error(f"[BiliBili推送] {up_name} 更新了动态 {up_last_dynid}，截图失败 {e}")
#             await app.sendFriendMessage(
#                 yaml_data["Basic"]["Permission"]["Master"],
#                 MessageChain.create(
#                     f"[BiliBili推送] {up_name}（{up_id}）的新动态 {up_last_dynid} 截图失败 {e}",
#                 ),
#             )
#             break
#         if up_id in sub_list:

#             if dyn.card_type == DynamicType.forward:
#                 type_text = "转发了一条动态！"
#             elif dyn.card_type == DynamicType.word:
#                 type_text = "发布了一条文字动态！"
#             elif dyn.card_type == DynamicType.draw:
#                 type_text = "发布了一条图文动态！"
#             elif dyn.card_type == DynamicType.article:
#                 type_text = "发布了一条专栏！"
#             elif dyn.card_type == DynamicType.av:
#                 type_text = "发布了一条新视频！"
#             else:
#                 type_text = "发布了一条动态！"

#             for groupid in sub_list[up_id]:
#                 if (
#                     yaml_data["Basic"]["Permission"]["Debug"]
#                     and groupid != yaml_data["Basic"]["Permission"]["DebugGroup"]
#                 ):
#                     continue
#                 try:
#                     await app.sendGroupMessage(
#                         groupid,
#                         MessageChain.create(
#                             [
#                                 Plain(f"本群订阅的UP {up_name}（{up_id}）{type_text}"),
#                                 Image(data_bytes=shot_image),
#                                 Plain(f"https://t.bilibili.com/{up_last_dynid}"),
#                             ]
#                         ),
#                     )
#                     await asyncio.sleep(1)
#                 except UnknownTarget:
#                     remove_list = []
#                     for subid in get_group_sublist(groupid):
#                         await remove_uid(subid, groupid)
#                         remove_list.append(subid)
#                     logger.info(
#                         f"[BiliBili推送] 推送失败，找不到该群 {groupid}，已删除该群订阅的 {len(remove_list)} 个UP"
#                     )
#                 except Exception as e:
#                     logger.info(f"[BiliBili推送] 推送失败，未知错误 {type(e)}")

#         elif yaml_data["Saya"]["BilibiliDynamic"]["AutoUnsubscribe"]:
#             logger.warning(f"[BiliBili推送] 没有找到订阅UP {up_name}（{up_id}）的群，已退订！")
#             resp = await relation_modify(up_id, 2)
#             if resp["code"] == 0:
#                 logger.info("[BiliBili推送] 退订成功！")
#                 await app.sendFriendMessage(
#                     yaml_data["Basic"]["Permission"]["Master"],
#                     MessageChain.create(
#                         f"[BiliBili推送] 未找到订阅 {up_name}（{up_id}）的群，已被退订！",
#                     ),
#                 )
#     # 将当前检测到的第一条动态 id 设置为最新的动态 id
#     OFFSET = int(dynall[0].extend.dyn_id_str)


# @channel.use(
#     ListenerSchema(
#         listening_events=[GroupMessage],
#         inline_dispatchers=[
#             Twilight(
#                 [
#                     RegexMatch(r"(订阅|关注)(主播|[uU][pP])?"),
#                     "anything" @ WildcardMatch(optional=True),
#                 ]
#             )
#         ],
#         decorators=[Permission.require(Permission.GROUP_ADMIN), Interval.require()],
#     )
# )
# async def add_sub(group: Group, anything: RegexResult):

#     if anything.matched:
#         add = await add_uid(anything.result.asDisplay(), group.id)
#         await safeSendGroupMessage(
#             group,
#             MessageChain.create(add),
#         )


# @channel.use(
#     ListenerSchema(
#         listening_events=[GroupMessage],
#         inline_dispatchers=[
#             Twilight(
#                 [
#                     RegexMatch(r"(退订|取关)(主播|[uU][pP])?"),
#                     "anything" @ WildcardMatch(optional=True),
#                 ]
#             )
#         ],
#         decorators=[Permission.require(Permission.GROUP_ADMIN), Interval.require()],
#     )
# )
# async def remove_sub(group: Group, anything: RegexResult):

#     if anything.matched:
#         await safeSendGroupMessage(
#             group,
#             MessageChain.create(await remove_uid(anything.result.asDisplay(), group.id)),
#         )


# @channel.use(
#     ListenerSchema(
#         listening_events=[GroupMessage],
#         inline_dispatchers=[Twilight(RegexMatch(r"本群(订阅|关注)列表"))],
#         decorators=[Permission.require(Permission.GROUP_ADMIN), Interval.require()],
#     )
# )
# async def sub_list(group: Group):

#     sublist = list(get_group_sublist(group.id))
#     sublist_count = len(sublist)
#     if sublist_count == 0:
#         await safeSendGroupMessage(group, MessageChain.create([Plain("本群未订阅任何 UP")]))
#     else:
#         await safeSendGroupMessage(
#             group,
#             MessageChain.create(
#                 [Plain(f"本群共订阅 {sublist_count} 个 UP\n"), Plain("\n".join(sublist))]
#             ),
#         )


# @channel.use(ListenerSchema(listening_events=[BotLeaveEventActive, BotLeaveEventKick]))
# async def bot_leave(group: Group):
#     remove_list = []
#     for subid in get_group_sublist(group.id):
#         remove_uid(subid, group.id)
#         remove_list.append(subid)
#     logger.info(
#         f"[BiliBili推送] 检测到退群事件 > {group.name}({group.id})，已删除该群订阅的 {len(remove_list)} 个UP"
#     )


# @channel.use(
#     ListenerSchema(
#         listening_events=[GroupMessage],
#         inline_dispatchers=[Twilight([FullMatch("查看动态"), "anything" @ WildcardMatch()])],
#         decorators=[Permission.require(), Interval.require(20)],
#     )
# )
# async def vive_dyn(group: Group, anything: RegexResult):

#     if not anything.matched:
#         return
#     pattern = re.compile("^[0-9]*$|com/([0-9]*)")
#     if match := pattern.search(anything.result.asDisplay()):
#         uid = match.group(1) or match.group(0)
#     else:
#         return await safeSendGroupMessage(
#             group, MessageChain.create([Plain("请输入正确的 UP UID 或 首页链接")])
#         )

#     res = await grpc_dyn_get(uid)
#     if res:
#         shot_image = await get_dynamic_screenshot(res["list"][0]["extend"]["dyn_id_str"])
#         await safeSendGroupMessage(
#             group, MessageChain.create([Image(data_bytes=shot_image)])
#         )
#     else:
#         await safeSendGroupMessage(group, MessageChain.create([Plain("该UP未发布任何动态")]))
