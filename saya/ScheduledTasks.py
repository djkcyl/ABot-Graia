from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.scheduler.timers import crontabify
from graia.ariadne.message.element import Plain
from graia.ariadne.message.chain import MessageChain
from graia.scheduler.saya.schema import SchedulerSchema


from config import yaml_data
from util.text2image import delete_old_cache
from database.db import reset_sign, all_sign_num, ladder_rent_collection


saya = Saya.current()
channel = Channel.current()


@channel.use(SchedulerSchema(crontabify("0 8 * * *")))
async def tasks(app: Ariadne):
    sign_info = await all_sign_num()
    await reset_sign()
    total_rent = ladder_rent_collection()
    cache, delete_cache = await delete_old_cache()
    await app.sendFriendMessage(
        yaml_data["Basic"]["Permission"]["Master"],
        MessageChain.create(
            [
                Plain(f"签到重置成功，昨日共有 {str(sign_info[0])} / {str(sign_info[1])} 人完成了签到，"),
                Plain(f"签到率为 {'{:.2%}'.format(sign_info[0]/sign_info[1])}\n"),
                Plain(f"今日收取了 {total_rent} 游戏币\n"),
                Plain(f"缓存清理 {delete_cache}/{cache} 个"),
            ],
        ),
    )
