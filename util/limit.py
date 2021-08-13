import time
import redis

from redis.exceptions import ConnectionError
from graia.application.group import Group, Member
from graia.application import GraiaMiraiApplication
from graia.broadcast.exceptions import ExecutionStop
from graia.broadcast.builtin.decorators import Depend
from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import At, Plain

try:
    r = redis.Redis(host='localhost', port=6379, db=6, decode_responses=True)
except ConnectionError:
    print("Redis 服务器连接失败，请检查 Redis 服务器是否正常运行")
r.flushdb()
BLOCK_LIST = []


def limit_exists(name, limit):

    now_time = int(time.time())
    if r.exists(name):
        last_time, limited = r.get(name).split("_")
        return True, int(last_time) + int(limited) - now_time, limited
    else:
        r.set(name, str(now_time) + "_" + str(limit), ex=limit)
        try:
            BLOCK_LIST.remove(name)
        except ValueError:
            pass
        return False, None, None


def member_limit_check(limit: int):
    async def limit_wrapper(app: GraiaMiraiApplication, group: Group, member: Member):
        name = str(group.id) + "_" + str(member.id)
        limit_blocked, cd, limited = limit_exists(name, limit)
        if limit_blocked:
            if name not in BLOCK_LIST:
                await app.sendGroupMessage(group, MessageChain.create([
                    At(member.id),
                    Plain(" 超过调用频率限制"),
                    Plain(f"\n你使用的上一个功能需要你冷却 {limited} 秒"),
                    Plain(f"\n剩余 {cd} 秒后可用")
                ]))
                BLOCK_LIST.append(name)
            raise ExecutionStop()
    return Depend(limit_wrapper)


def group_limit_check(limit: int):
    async def limit_wrapper(app: GraiaMiraiApplication, group: Group):
        name = str(group.id)
        limit_blocked, cd, limited = limit_exists(name, limit)
        if limit_blocked:
            if name not in BLOCK_LIST:
                await app.sendGroupMessage(group, MessageChain.create([
                    Plain("超过调用频率限制"),
                    Plain(f"\n本群的上一个功能需要冷却 {limited} 秒"),
                    Plain(f"\n剩余 {cd} 秒后可用")
                ]))
                BLOCK_LIST.append(name)
            raise ExecutionStop()
    return Depend(limit_wrapper)


def manual_limit(group, func, limit: int):
    name = str(group) + "_" + func
    limit_blocked, _, _ = limit_exists(name, limit)
    if limit_blocked:
        raise ExecutionStop()