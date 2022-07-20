import asyncio
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.scheduler.timers import crontabify
from graia.ariadne.event.message import FriendMessage
from graia.ariadne.message.chain import MessageChain
from graia.scheduler.saya.schema import SchedulerSchema
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import Twilight, FullMatch

from util.control import Permission
from util.text2image import delete_old_cache
from util.sendMessage import safeSendGroupMessage
from config import COIN_NAME, yaml_data, group_list
from database.db import activity_count, ladder_rent_collection, reset_sign

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[FriendMessage],
        inline_dispatchers=[Twilight([FullMatch("执行定时任务")])],
        decorators=[Permission.require(Permission.MASTER)],
    )
)
@channel.use(SchedulerSchema(crontabify("0 4 * * *")))
async def tasks(app: Ariadne):
    sign_info = await activity_count()
    await reset_sign()
    total_rent = ladder_rent_collection()
    cache, delete_cache = delete_old_cache()
    await app.sendFriendMessage(
        yaml_data["Basic"]["Permission"]["Master"],
        MessageChain.create(
            "签到重置成功\n",
            f"签到率 {str(sign_info[1])} / {str(sign_info[0])} {'{:.2%}'.format(sign_info[1]/sign_info[0])}\n",
            f"活跃率 {str(sign_info[2])} / {str(sign_info[0])} {'{:.2%}'.format(sign_info[2]/sign_info[0])}\n",
            f"活跃签到率 {str(sign_info[1])} / {str(sign_info[2])} {'{:.2%}'.format(sign_info[1]/sign_info[2])}\n",
            f"今日收取了 {total_rent} {COIN_NAME}\n",
            f"缓存清理 {delete_cache}/{cache} 个",
        ),
    )


@channel.use(SchedulerSchema(crontabify("* * * * *")))
async def clean_group(app: Ariadne):
    get_group_list = await app.getGroupList()
    i = 0
    for group in get_group_list:
        member_count = len(await app.getMemberList(group))
        if member_count < 15 and group.id not in group_list["white"]:
            try:
                await safeSendGroupMessage(
                    group,
                    MessageChain.create(
                        f'{yaml_data["Basic"]["BotName"]} 当前暂不加入群人数低于 15 的群，正在退出'
                    ),
                )
                await app.quitGroup(group)
            except Exception as e:
                await app.sendFriendMessage(
                    yaml_data["Basic"]["Permission"]["Master"],
                    MessageChain.create(f"群 {group.name}({group.id}) 退出失败\n{e}"),
                )
            else:
                await app.sendFriendMessage(
                    yaml_data["Basic"]["Permission"]["Master"],
                    MessageChain.create(
                        f"群 {group.name}({group.id}) 退出成功\n当前群人数 {member_count}"
                    ),
                )
            i += 1
            await asyncio.sleep(0.3)
    if i != 0:
        await app.sendFriendMessage(
            yaml_data["Basic"]["Permission"]["Master"],
            MessageChain.create(f"本次共清理了 {i}/{len(get_group_list)} 个群"),
        )
