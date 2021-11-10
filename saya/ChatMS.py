# import httpx
# import random
# import asyncio

# from loguru import logger
# from graia.saya import Saya, Channel
# from graia.ariadne.app import Ariadne
# from graia.ariadne.model import Group, Member
# from graia.scheduler.timers import crontabify
# from graia.ariadne.message.element import At, Plain
# from graia.ariadne.message.chain import MessageChain
# from graia.ariadne.event.message import GroupMessage
# from graia.scheduler.saya.schema import SchedulerSchema
# from graia.saya.builtins.broadcast.schema import ListenerSchema

# from config import yaml_data, group_data

# from util.control import Permission, Interval
# from util.sendMessage import safeSendGroupMessage


# saya = Saya.current()
# channel = Channel.current()

# logger.info("正在下载词库")
# root = httpx.get(
#     "https://raw.githubusercontents.com/Kyomotoi/AnimeThesaurus/main/data.json",
#     verify=False,
# ).json()


# @channel.use(SchedulerSchema(crontabify("0 0 * * *")))
# async def updateDict():
#     global root
#     await asyncio.sleep(1)
#     logger.info(msg=f"已更新完成聊天词库，共计：{len(root)}条")


# @channel.use(
#     ListenerSchema(listening_events=[GroupMessage], decorators=[Permission.require()])
# )
# async def main(app: Ariadne, group: Group, member: Member, message: MessageChain):

#   if (
#       yaml_data["Saya"]["ChatMS"]["Disabled"]
#       and group.id != yaml_data["Basic"]["Permission"]["DebugGroup"]
#   ):
#       return


#     elif "ChatMS" in group_data[str(group.id)]["DisabledFunc"]:
#         return

#     if message.has(At):
#         if message.getFirst(At).target == yaml_data["Basic"]["MAH"]["BotQQ"]:
#             saying = message.getFirst(Plain).text
#             for key in root:
#                 if key in saying:
#                     await Interval.manual(member.id)
#                     return await safeSendGroupMessage(
#                         group, MessageChain.create([Plain(random.choice(root[key]))])
#                     )
