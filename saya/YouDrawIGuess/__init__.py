from graia.application import GraiaMiraiApplication
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.event.messages import *
from graia.application.event.mirai import *
from graia.application.message.elements.internal import *
from graia.application.message.parser.literature import Literature
from graia.broadcast.interrupt import InterruptControl
from graia.broadcast.interrupt.waiter import Waiter

from config import yaml_data

saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
inc = InterruptControl(bcc)


GROUP_RUNING_LIST = []
GROUP_GAME_PROCESS = []


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("你画asdasdxczxv我猜")]))
async def main(app: GraiaMiraiApplication, group: Group, member: Member):

    # 请求确认中断
    @Waiter.create_using_function([GroupMessage])
    async def confirm(confirm_group: Group, confirm_member: Member, confirm_message: MessageChain):
        if all([confirm_group.id == group.id,
                confirm_member.id == member.id]):
            saying = confirm_message.asDisplay()
            if saying == "是":
                return True
            elif saying == "否":
                return False
            else:
                await app.sendGroupMessage(group, MessageChain.create([Plain("请发送是或否来进行确认")]))

    # 如果当前群有一个正在进行中的游戏
    if group.id in GROUP_RUNING_LIST:
        await app.sendGroupMessage(group, MessageChain.create([
            Plain("当前群聊存在一场已经开始的游戏，是否加入？这将消耗你 1 个游戏币")
        ]))

    else:
        await app.sendGroupMessage(group, MessageChain.create([Plain("确认开启一场你画我猜？这将消耗你 4 个游戏币")]))

        try:
            if await asyncio.wait_for(inc.wait(confirm), timeout=10):  # 如果 10 秒内无响应
                await app.sendGroupMessage(group, MessageChain.create([Plain("已确认，你已加入到当前游戏中")]))
            else:
                await app.sendGroupMessage(group, MessageChain.create([Plain("已拒绝")]))

        except asyncio.TimeoutError:
            await app.sendGroupMessage(group, MessageChain.create([Plain("确认超时")]))
