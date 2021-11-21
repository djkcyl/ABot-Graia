import asyncio

from datetime import datetime
from graia.saya import Saya, Channel
from graia.ariadne.message.element import At
from graia.ariadne.model import Group, Member
from graia.broadcast.interrupt.waiter import Waiter
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import GroupMessage
from graia.broadcast.interrupt import InterruptControl
from graia.scheduler.timers import every_custom_seconds
from graia.scheduler.saya.schema import SchedulerSchema
from graia.ariadne.message.parser.literature import Literature
from graia.saya.builtins.broadcast.schema import ListenerSchema


from config import yaml_data, group_data
from util.control import Permission, Interval
from util.sendMessage import safeSendGroupMessage

from .time_parser import time_parser
from .db import add_reminder, get_undone_reminder, set_reminder_completed


saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
inc = InterruptControl(bcc)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Literature("新建提醒")],
        decorators=[Permission().require(), Interval().require()],
    )
)
async def main(group: Group, member: Member):

    if (
        yaml_data["Saya"]["Reminder"]["Disabled"]
        and group.id != yaml_data["Basic"]["Permission"]["DebugGroup"]
    ):
        return
    elif "Reminder" in group_data[str(group.id)]["DisabledFunc"]:
        return

    @Waiter.create_using_function([GroupMessage])
    async def message_waiter(
        waiter1_group: Group, waiter1_member: Member, waiter1_message: MessageChain
    ):
        if waiter1_group.id == group.id and waiter1_member.id == member.id:
            if waiter1_message.asDisplay() == "取消":
                return False
            else:
                return waiter1_message.asDisplay()

    try:
        await safeSendGroupMessage(group, MessageChain.create("请在60秒内发送需要提醒的时间"))
        time_waiter = await asyncio.wait_for(inc.wait(message_waiter), 60)
        if time_waiter:
            time = await time_parser(time_waiter)
            print(time)
            if time:
                if datetime.strptime(time, "%Y-%m-%d %H:%M:%S") < datetime.now():
                    await safeSendGroupMessage(
                        group, MessageChain.create(f"提醒时间 {time} 不能小于当前时间")
                    )
                else:
                    await safeSendGroupMessage(
                        group, MessageChain.create("请在60秒内发送要提醒的内容")
                    )
                    content_waiter = await asyncio.wait_for(
                        inc.wait(message_waiter), 60
                    )
                    if content_waiter:
                        thing = add_reminder(
                            member.id,
                            group.id,
                            time,
                            content_waiter,
                        )
                        await safeSendGroupMessage(
                            group,
                            MessageChain.create(
                                At(member.id),
                                f" 提醒事件 ID:{thing} 创建成功，将在 {time} 提醒你 {content_waiter}",
                            ),
                        )
                    else:
                        await safeSendGroupMessage(group, MessageChain.create("已取消"))
            else:
                await safeSendGroupMessage(
                    group, MessageChain.create("时间输入有误，或包含不止一个时间")
                )
        else:
            await safeSendGroupMessage(group, MessageChain.create("已取消"))
    except asyncio.TimeoutError:
        await safeSendGroupMessage(group, MessageChain.create("等待超时"))


@channel.use(SchedulerSchema(every_custom_seconds(10)))
async def scheduler():
    for thing in get_undone_reminder():
        await safeSendGroupMessage(
            thing.group,
            MessageChain.create(
                At(thing.member),
                f" 你在 {thing.start_date} 创建了这个提醒，请注意查看\n==================\n{thing.thing}",
            ),
        )
        set_reminder_completed(thing.id)
        await asyncio.sleep(0.3)
