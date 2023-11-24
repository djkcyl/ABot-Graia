import random
import asyncio

from graia.saya import Channel, Saya
from graia.ariadne.message.element import At
from graia.ariadne.model import Group, Member
from graia.broadcast.interrupt.waiter import Waiter
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import GroupMessage
from graia.broadcast.interrupt import InterruptControl
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import FullMatch, Twilight

from database.db import add_answer
from core_bak.control import Permission, Function
from util.sendMessage import safeSendGroupMessage

from .data import data

saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
inc = InterruptControl(bcc)


RUNNING = {}


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("背成语")])],
        decorators=[Permission.require(), Function.require("IdiomTest")],
    )
)
async def group_learn(group: Group):
    @Waiter.create_using_function(
        listening_events=[GroupMessage],
        using_decorators=[Permission.require()],
        block_propagation=True,
    )
    async def waiter(
        waiter_group: Group, waiter_member: Member, waiter_message: MessageChain
    ):
        if waiter_group.id == group.id:
            waiter_saying = waiter_message.asDisplay().strip()
            if waiter_saying == "取消":
                return False
            elif waiter_saying == RUNNING[group.id]:
                return waiter_member.id

    if group.id in RUNNING:
        return

    RUNNING[group.id] = None

    while True:
        word_data = random.choice(data)
        RUNNING[group.id] = word_data["word"]

        await safeSendGroupMessage(
            group,
            MessageChain.create(
                f"本回合题目：\n该成语释义：{word_data['explanation']}\n",
                f"出处：{word_data['derivation'].replace(word_data['word'], '*' * len(word_data['word']))}",
            ),
        )
        try:
            answer_qq = await asyncio.wait_for(inc.wait(waiter), timeout=60)
            if answer_qq:
                await add_answer(str(answer_qq))
                await safeSendGroupMessage(
                    group,
                    MessageChain.create(
                        "恭喜 ",
                        At(answer_qq),
                        f" 回答正确 {word_data['word']}",
                    ),
                )
                await asyncio.sleep(2)
            else:
                del RUNNING[group.id]
                return await safeSendGroupMessage(group, MessageChain.create("已结束本次答题"))

        except asyncio.TimeoutError:
            del RUNNING[group.id]
            return await safeSendGroupMessage(
                group,
                MessageChain.create(
                    f"本次成语为：{word_data['word']}\n",
                    f"这个成语出自：{word_data['derivation']}\n",
                    f"释义：{word_data['explanation']}\n",
                    f"读音：{word_data['pinyin']}\n",
                    "答题已结束，请重新开启",
                ),
            )
