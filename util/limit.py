import time
import redis

from graia.application import GraiaMiraiApplication
from graia.broadcast.exceptions import ExecutionStop
from graia.broadcast.builtin.decorators import Depend
from graia.application.group import Group, Member
from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import At, Plain
from redis.exceptions import ConnectionError

try:
    r = redis.Redis(host='localhost', port=6379, db=6, decode_responses=True)
except ConnectionError:
    print("Redis 服务器连接失败，请检查 Redis 服务器是否正常运行")
r.flushdb()
BLOCK_LIST = []

def limit_exists(name, limit):
    
    now_time = int(time.time())
    if r.exists(name):
        last_time = int(r.get(name))
        return True, last_time + limit - now_time
    else:
        now_time = int(time.time())
        r.set(name, now_time, ex=limit)
        try:
            BLOCK_LIST.remove(name)
        except ValueError:
            pass
        return False, None


def member_limit_check(limit: int):

    async def limit_wrapper(app: GraiaMiraiApplication, group: Group, member: Member):
        name = str(group.id) + "_" + str(member.id)
        limit_blocked, cd = limit_exists(name, limit)
        if limit_blocked:
            print(2)
            if name not in BLOCK_LIST:
                await app.sendGroupMessage(group, MessageChain.create([
                    At(member.id),
                    Plain(" 超过调用频率限制"),
                    Plain(f"\n该功能在 {str(limit)} 秒内仅可使用一次"),
                    Plain(f"\n剩余 {cd} 秒后可用")
                ]))
                BLOCK_LIST.append(name)
            raise ExecutionStop()
    return Depend(limit_wrapper)
