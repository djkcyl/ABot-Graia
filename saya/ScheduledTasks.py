import asyncio
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.scheduler.timers import crontabify
from graia.ariadne.message.chain import MessageChain
from graia.scheduler.saya.schema import SchedulerSchema

from util.text2image import delete_old_cache
from util.sendMessage import safeSendGroupMessage
from config import COIN_NAME, yaml_data, group_list
from database.db import all_sign_num, ladder_rent_collection, reset_sign

channel = Channel.current()


@channel.use(SchedulerSchema(crontabify("0 4 * * *")))
async def tasks(app: Ariadne):
    sign_info = await all_sign_num()
    await reset_sign()
    total_rent = ladder_rent_collection()
    cache, delete_cache = delete_old_cache()
    await app.sendFriendMessage(
        yaml_data["Basic"]["Permission"]["Master"],
        MessageChain.create(
            f"签到重置成功，昨日共有 {str(sign_info[0])} / {str(sign_info[1])} 人完成了签到，",
            f"签到率为 {'{:.2%}'.format(sign_info[0]/sign_info[1])}\n",
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
