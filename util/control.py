# coding=utf-8
"""
Xenon 管理 https://github.com/McZoo/Xenon/blob/master/lib/control.py
"""

import time
import random

from asyncio import Lock
from typing import Optional
from datetime import datetime
from graia.saya import Channel
from collections import defaultdict
from graia.ariadne.app import Ariadne
from graia.scheduler.timers import crontabify
from typing import DefaultDict, Set, Tuple, Union
from graia.broadcast.exceptions import ExecutionStop
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import GroupMessage
from graia.broadcast.builtin.decorators import Depend
from graia.scheduler.saya.schema import SchedulerSchema
from graia.ariadne.message.element import Plain, Source
from graia.ariadne.model import Friend, Member, MemberPerm

from config import user_list, yaml_data, group_data

from .sendMessage import safeSendGroupMessage

channel = Channel.current()


SLEEP = 0
BOT_SHUTDOWN = False


def bot_shutdown(shutdown=None):
    global BOT_SHUTDOWN
    if shutdown is None:
        return BOT_SHUTDOWN
    elif shutdown:
        BOT_SHUTDOWN = True
    else:
        BOT_SHUTDOWN = False


@channel.use(SchedulerSchema(crontabify("30 7 * * *")))
async def work_scheduled(app: Ariadne):
    Rest.set_sleep(0)
    await app.sendFriendMessage(
        yaml_data["Basic"]["Permission"]["Master"],
        MessageChain.create([Plain("已退出休息时间")]),
    )


@channel.use(SchedulerSchema(crontabify("0 0 * * *")))
async def rest_scheduled(app: Ariadne):
    Rest.set_sleep(1)
    await app.sendFriendMessage(
        yaml_data["Basic"]["Permission"]["Master"],
        MessageChain.create([Plain("已进入休息时间")]),
    )


class Rest:
    """
    用于控制睡眠的类，不应被实例化
    """

    @staticmethod
    def set_sleep(sleep):
        global SLEEP
        SLEEP = sleep

    @staticmethod
    def rest_control(zzzz: bool = True):
        async def sleep(event: GroupMessage):
            if (
                SLEEP
                and yaml_data["Basic"]["Permission"]["Rest"]
                and event.sender.group.id
                != yaml_data["Basic"]["Permission"]["DebugGroup"]
            ):
                if zzzz:
                    await safeSendGroupMessage(
                        event.sender.group,
                        MessageChain.create(
                            f"Z{'z'*random.randint(3,8)}{'.'*random.randint(2,6)}"
                        ),
                        quote=event.messageChain.getFirst(Source).id,
                    )
                raise ExecutionStop()

        return Depend(sleep)


# 用于控制功能开关的类
class Function:
    """
    用于功能管理的类，不应该被实例化
    """
    @staticmethod
    def require(funcname: str) -> Depend:
        def func_check(member: Member):
            if member.id == yaml_data["Basic"]["Permission"]["Master"]:
                return
            if bot_shutdown():
                raise ExecutionStop()
            elif yaml_data["Saya"][funcname]["Disabled"]:
                raise ExecutionStop()
            elif funcname in group_data[str(member.group.id)]["DisabledFunc"]:
                raise ExecutionStop()

        return Depend(func_check)


class RollQQ:
    """
    用于功能单双号限制的类，不应该被实例化
    """

    def require() -> Depend:
        def qq_check(member: Member):
            day = datetime.now().day
            if member.id == yaml_data["Basic"]["Permission"]["Master"]:
                pass
            elif (day % 2) == 0 and (member.id % 2) == 0:
                pass
            elif day % 2 == 0 or member.id % 2 == 0:
                raise ExecutionStop()

        return Depend(qq_check)


class Permission:
    """
    用于管理权限的类，不应被实例化
    """

    MASTER = 30
    GROUP_ADMIN = 20
    USER = 10
    BANNED = 0
    DEFAULT = USER

    @classmethod
    def get(cls, member: Union[Member, int]) -> int:
        """
        获取用户的权限

        :param user: 用户实例或QQ号
        :return: 等级，整数
        """

        if isinstance(member, Member):
            user = member.id
            user_permission = member.permission
        if isinstance(member, int):
            user = member
            user_permission = cls.DEFAULT

        if user == 80000000:
            raise ExecutionStop()

        if user in yaml_data["Basic"]["Permission"]["Admin"]:
            return cls.MASTER
        elif user in user_list["black"]:
            return cls.BANNED
        elif user_permission in [MemberPerm.Administrator, MemberPerm.Owner]:
            return cls.GROUP_ADMIN
        else:
            return cls.DEFAULT

    @classmethod
    def require(cls, level: int = DEFAULT) -> Depend:
        """
        指示需要 `level` 以上等级才能触发，默认为至少 USER 权限

        :param level: 限制等级
        """

        def perm_check(event: GroupMessage):
            member_level = cls.get(event.sender)

            if (
                yaml_data["Basic"]["Permission"]["Debug"]
                and event.sender.group.id
                != yaml_data["Basic"]["Permission"]["DebugGroup"]
            ):
                raise ExecutionStop()
            if member_level >= level:
                return
            raise ExecutionStop()

        return Depend(perm_check)

    @classmethod
    def manual(cls, member: Union[Member, Friend, int], level: int = DEFAULT) -> Depend:

        if isinstance(member, Member):
            member_id = member.id
        if isinstance(member, Friend):
            member_id = member.id
        if isinstance(member, int):
            member_id = member

        member_level = cls.get(member_id)

        if isinstance(member, Member) and (
            yaml_data["Basic"]["Permission"]["Debug"]
            and member.group.id != yaml_data["Basic"]["Permission"]["DebugGroup"]
        ):
            raise ExecutionStop()
        if member_level >= level:
            return
        raise ExecutionStop()


class Interval:
    """
    用于冷却管理的类，不应被实例化
    """

    last_exec: DefaultDict[int, Tuple[int, float]] = defaultdict(lambda: (1, 0.0))
    sent_alert: Set[int] = set()
    lock: Optional[Lock] = None

    @classmethod
    async def get_lock(cls):
        if not cls.lock:
            cls.lock = Lock()
        return cls.lock

    @classmethod
    def require(
        cls,
        suspend_time: float = 10,
        max_exec: int = 1,
        override_level: int = Permission.MASTER,
        silent: bool = False,
    ):
        """
        指示用户每执行 `max_exec` 次后需要至少相隔 `suspend_time` 秒才能再次触发功能

        等级在 `override_level` 以上的可以无视限制

        :param suspend_time: 冷却时间
        :param max_exec: 在再次冷却前可使用次数
        :param override_level: 可超越限制的最小等级
        """

        async def cd_check(event: GroupMessage):
            if Permission.get(event.sender) >= override_level:
                return
            current = time.time()
            async with (await cls.get_lock()):
                last = cls.last_exec[event.sender.id]
                if current - cls.last_exec[event.sender.id][1] >= suspend_time:
                    cls.last_exec[event.sender.id] = (1, current)
                    if event.sender.id in cls.sent_alert:
                        cls.sent_alert.remove(event.sender.id)
                    return
                elif last[0] < max_exec:
                    cls.last_exec[event.sender.id] = (last[0] + 1, current)
                    if event.sender.id in cls.sent_alert:
                        cls.sent_alert.remove(event.sender.id)
                    return
                if event.sender.id not in cls.sent_alert:
                    # if not silent:
                    #     await safeSendGroupMessage(
                    #         event.sender.group,
                    #         MessageChain.create(
                    #             [
                    #                 Plain(
                    #                     f"冷却还有{last[1] + suspend_time - current:.2f}秒结束，"
                    #                     f"之后可再执行{max_exec}次"
                    #                 )
                    #             ]
                    #         ),
                    #         quote=event.messageChain.getFirst(Source).id,
                    #     )
                    cls.sent_alert.add(event.sender.id)
                raise ExecutionStop()

        return Depend(cd_check)

    @classmethod
    async def manual(
        cls,
        member: Union[Member, int],
        suspend_time: float = 10,
        max_exec: int = 1,
        override_level: int = Permission.MASTER,
    ):
        if Permission.get(member) >= override_level:
            return
        current = time.time()
        async with (await cls.get_lock()):
            last = cls.last_exec[member]
            if current - cls.last_exec[member][1] >= suspend_time:
                cls.last_exec[member] = (1, current)
                if member in cls.sent_alert:
                    cls.sent_alert.remove(member)
                return
            elif last[0] < max_exec:
                cls.last_exec[member] = (last[0] + 1, current)
                if member in cls.sent_alert:
                    cls.sent_alert.remove(member)
                return
            if member not in cls.sent_alert:
                cls.sent_alert.add(member)
            raise ExecutionStop()
