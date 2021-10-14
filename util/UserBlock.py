from typing import Optional, Any, Union
from graia.application.friend import Friend
from graia.application.group import Group, Member
from graia.broadcast.exceptions import ExecutionStop
from graia.broadcast.builtin.decorators import Depend

from config import user_black_list

group_black_list = [579037216, 757689154]


def group_black_list_block():
    '''
    黑名单
    ~~~~~~~~~~~~~~~~~~~~~
    在名單內的群和用戶机器人将会始终忽略的控制方式
    '''
    async def _block(group: Group, member: Member):
        if group.id in group_black_list or member.id in user_black_list:
            raise ExecutionStop()
    return Depend(_block)

def friend_black_list_block():
    '''
    黑名单
    ~~~~~~~~~~~~~~~~~~~~~
    在名單內的用戶机器人将会始终忽略的控制方式
    '''
    async def _block(friend: Friend):
        if friend.id in user_black_list:
            raise ExecutionStop()
    return Depend(_block)

def manual_block(memberid=None, groupid=None):
    '''
    手动黑名单
    ~~~~~~~~~~~~~~~~~~~~~
    当 `group_black_list_block()` 无法使用时可用此方法
    '''
    if groupid in group_black_list or memberid in user_black_list:
        raise ExecutionStop()
