import random

from loguru import logger
from graia.saya import Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group, Member
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import AtAll, Plain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import FullMatch, Twilight

from config import yaml_data
from util.time_tools import calc_time_total
from core.control import Function, Interval
from util.sendMessage import safeSendGroupMessage

channel = Channel.current()

if (
    yaml_data["Saya"]["MutePack"]["MaxTime"]
    * yaml_data["Saya"]["MutePack"]["MaxMultiple"]
    * yaml_data["Saya"]["MutePack"]["MaxSuperDoubleMultiple"]
    > 2592000
):
    logger.error("禁言套餐最大时长设定超过30天，请检查配置文件")
    exit()

t = r"(?=.*要)(?=.*禁)(?=.*言)(?=.*套)(?=.*餐)"


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch(r"我要禁言套餐")])],
        decorators=[Function.require("MutePack"), Interval.require()],
    )
)
async def random_mute(app: Ariadne, group: Group, member: Member):
    if member.id in yaml_data["Basic"]["Permission"]["Admin"]:
        await safeSendGroupMessage(group, MessageChain.create([Plain("我不能这样做！")]))
    else:
        time = random.randint(60, yaml_data["Saya"]["MutePack"]["MaxTime"])
        multiple = random.randint(1, yaml_data["Saya"]["MutePack"]["MaxMultiple"])
        ftime = time * multiple
        srtftime = calc_time_total(ftime * 1000)
        if (
            random.randint(1, yaml_data["Saya"]["MutePack"]["MaxJackpotProbability"])
            == yaml_data["Saya"]["MutePack"]["MaxJackpotProbability"]
        ):
            try:
                await app.muteMember(group, member, 2592000)
                await safeSendGroupMessage(
                    group,
                    MessageChain.create(
                        [AtAll(), Plain(f"恭喜{member.name}中了头奖！获得30天禁言！")]
                    ),
                )
                quit()
            except PermissionError:
                await safeSendGroupMessage(
                    group,
                    MessageChain.create(
                        [
                            Plain(
                                f"权限不足，无法使用！\n使用该功能{yaml_data['Basic']['BotName']}需要为管理"
                            )
                        ]
                    ),
                )
        elif (
            yaml_data["Saya"]["MutePack"]["SuperDouble"]
            and random.randint(
                1, yaml_data["Saya"]["MutePack"]["MaxSuperDoubleProbability"]
            )
            == yaml_data["Saya"]["MutePack"]["MaxSuperDoubleProbability"]
        ):
            try:
                ftime = ftime * yaml_data["Saya"]["MutePack"]["MaxSuperDoubleMultiple"]
                srtftime = calc_time_total(ftime * 1000)
                await app.muteMember(group, member, ftime)
                await safeSendGroupMessage(
                    group,
                    MessageChain.create(
                        [
                            Plain(
                                f"恭喜你抽中了 {time} 秒禁言套餐！倍率为 {multiple}！\n超级加倍！\n最终时长为 {srtftime}"
                            )
                        ]
                    ),
                )
            except PermissionError:
                await safeSendGroupMessage(
                    group,
                    MessageChain.create(
                        [
                            Plain(
                                f"权限不足，无法使用！\n使用该功能{yaml_data['Basic']['BotName']}需要为管理员权限或更高"
                            )
                        ]
                    ),
                )
        else:
            try:
                await app.muteMember(group, member, ftime)
                await safeSendGroupMessage(
                    group,
                    MessageChain.create(
                        [Plain(f"恭喜你抽中了 {time} 秒禁言套餐！倍率为 {multiple}\n最终时长为 {srtftime}")]
                    ),
                )
            except PermissionError:
                await safeSendGroupMessage(
                    group,
                    MessageChain.create(
                        [
                            Plain(
                                f"权限不足，无法使用！\n使用该功能{yaml_data['Basic']['BotName']}需要为管理员权限或更高"
                            )
                        ]
                    ),
                )
