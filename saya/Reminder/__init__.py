import asyncio

from datetime import datetime
from graia.saya import Saya, Channel
from graia.ariadne.model import Group, Member
from graia.ariadne.message.element import At, Plain
from graia.broadcast.interrupt.waiter import Waiter
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import GroupMessage
from graia.broadcast.interrupt import InterruptControl
from graia.scheduler.timers import every_custom_seconds
from graia.scheduler.saya.schema import SchedulerSchema
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import Twilight, FullMatch, WildcardMatch

from config import yaml_data, group_data
from util.control import Permission, Interval
from util.sendMessage import safeSendGroupMessage

from .time_parser import time_parser
from .db import (
    add_reminder,
    get_all_reminder,
    get_undone_reminder,
    set_reminder_deleted,
    set_reminder_completed,
)


saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
inc = InterruptControl(bcc)


@channel.use(SchedulerSchema(every_custom_seconds(10)))
async def scheduler():
    for thing in get_undone_reminder():
        try:
            await safeSendGroupMessage(
                thing.group,
                MessageChain.create(
                    At(thing.member),
                    f" 你在 {thing.start_date} 创建了这个提醒，请注意查看\n==================\n{thing.thing}",
                ),
            )
        except Exception:
            pass
        set_reminder_completed(thing.id)
        await asyncio.sleep(0.3)


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight({"head": FullMatch("定时提醒")})],
        decorators=[Permission().require(), Interval().require()],
    )
)
async def get_reminder(group: Group, member: Member):

    if (
        yaml_data["Saya"]["Reminder"]["Disabled"]
        and group.id != yaml_data["Basic"]["Permission"]["DebugGroup"]
    ):
        return
    elif "Reminder" in group_data[str(group.id)]["DisabledFunc"]:
        return

    reminders = get_all_reminder(member.id)
    if len(reminders) == 0:
        msg = "你没有创建需要提醒的内容，如需创建请发送“新建提醒”"
    else:
        msg = [At(member.id), Plain("你当前有以下提醒内容")]
        for reminder in reminders:
            msg.append(
                Plain(
                    f"\n===============\nID：{reminder.id}\n创建时间：{reminder.start_date}\n内容：{reminder.thing}\n到期时间：{reminder.end_date}"
                )
            )
        msg.append(Plain("\n===============\n如需删除请发送“删除提醒 <ID>”"))
    await safeSendGroupMessage(group, MessageChain.create(msg))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight({"head": FullMatch("新建提醒")})],
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
                        if thing:
                            await safeSendGroupMessage(
                                group,
                                MessageChain.create(
                                    At(member.id),
                                    f" 提醒事件 ID:{thing} 创建成功，将在 {time} 提醒你 {content_waiter}",
                                ),
                            )
                        else:
                            await safeSendGroupMessage(
                                group,
                                MessageChain.create(At(member.id), "每人最多创建 5 个定时任务"),
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


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                {"head": FullMatch("删除提醒"), "anything": WildcardMatch(optional=True)}
            )
        ],
        decorators=[Permission().require(), Interval().require()],
    )
)
async def del_reminder(group: Group, member: Member, anything: WildcardMatch):

    if (
        yaml_data["Saya"]["Reminder"]["Disabled"]
        and group.id != yaml_data["Basic"]["Permission"]["DebugGroup"]
    ):
        return
    elif "Reminder" in group_data[str(group.id)]["DisabledFunc"]:
        return

    if anything.matched:
        say = anything.result.asDisplay()
        if say.isdigit():
            thing = int(say)
            if set_reminder_deleted(thing):
                await safeSendGroupMessage(
                    group,
                    MessageChain.create(At(member.id), f" 提醒事件 ID:{thing} 删除成功"),
                )
            else:
                await safeSendGroupMessage(
                    group,
                    MessageChain.create(At(member.id), f" 提醒事件 ID:{thing} 不存在"),
                )
        else:
            await safeSendGroupMessage(
                group,
                MessageChain.create(At(member.id), " 提醒事件 ID 仅可为数字"),
            )
    else:
        await safeSendGroupMessage(
            group, MessageChain.create(At(member.id), " 请输入“删除提醒 <ID>”")
        )
