import random
import asyncio

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group, Member
from graia.broadcast.interrupt.waiter import Waiter
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.broadcast.interrupt import InterruptControl
from graia.ariadne.message.element import Plain, At, Image
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.lifecycle import ApplicationShutdowned
from graia.ariadne.message.parser.twilight import Twilight, FullMatch

from util.control import Permission, Interval
from database.db import reduce_gold, add_gold
from util.sendMessage import safeSendGroupMessage
from config import yaml_data, group_data, COIN_NAME

from .game import draw_game, run_game


saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
inc = InterruptControl(bcc)

MEMBER_RUNING_LIST = []
GROUP_RUNING_LIST = []
GROUP_GAME_PROCESS = {}


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight({"head": FullMatch("赛马")})],
        decorators=[Permission.require(), Interval.require()],
    )
)
async def horse_racing(group: Group):
    await safeSendGroupMessage(
        group, MessageChain.create("赛马小游戏！\n发送“开始赛马”加入游戏\n发送“退出赛马”可以退出已加入的游戏或解散房间")
    )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight({"head": FullMatch("开始赛马")})],
        decorators=[Permission.require(), Interval.require(30)],
    )
)
async def main(app: Ariadne, group: Group, member: Member):

    if (
        yaml_data["Saya"]["HorseRacing"]["Disabled"]
        and group.id != yaml_data["Basic"]["Permission"]["DebugGroup"]
    ):
        return
    elif "HorseRacing" in group_data[str(group.id)]["DisabledFunc"]:
        return

    @Waiter.create_using_function([GroupMessage])
    async def waiter1(
        waiter1_group: Group, waiter1_member: Member, waiter1_message: MessageChain
    ):
        if waiter1_group.id == group.id:
            if waiter1_message.asDisplay() == "加入赛马":
                player_list = GROUP_GAME_PROCESS[group.id]["members"]
                player_count = len(player_list)
                if waiter1_member.id in GROUP_GAME_PROCESS[group.id]["members"]:
                    await safeSendGroupMessage(
                        group, MessageChain.create("你已经参与了本轮游戏，请不要重复加入")
                    )
                else:
                    if await reduce_gold(str(waiter1_member.id), 5):
                        GROUP_GAME_PROCESS[group.id]["members"].append(
                            waiter1_member.id
                        )
                        player_list = GROUP_GAME_PROCESS[group.id]["members"]
                        player_count = len(player_list)
                        if 6 > player_count > 1:
                            GROUP_GAME_PROCESS[group.id]["status"] = "pre_start"
                            add_msg = "，发起者可发送“提前开始”来强制开始本场游戏"
                        else:
                            GROUP_GAME_PROCESS[group.id]["status"] = "waiting"
                            add_msg = ""
                        await safeSendGroupMessage(
                            group,
                            MessageChain.create(
                                At(waiter1_member.id),
                                Plain(
                                    f" 你已成功加入本轮游戏，当前共有 {player_count} / 6 人参与{add_msg}"
                                ),
                            ),
                        )
                        if player_count == 6:
                            GROUP_GAME_PROCESS[group.id]["status"] = "running"
                            return True
                    else:
                        await safeSendGroupMessage(
                            group, MessageChain.create(f"你的{COIN_NAME}不足，无法参加游戏")
                        )
            elif waiter1_message.asDisplay() == "退出赛马":
                player_list = GROUP_GAME_PROCESS[group.id]["members"]
                player_count = len(player_list)
                if waiter1_member.id == member.id:
                    for player in GROUP_GAME_PROCESS[group.id]["members"]:
                        await add_gold(str(player), 5)
                    MEMBER_RUNING_LIST.remove(member.id)
                    GROUP_RUNING_LIST.remove(group.id)
                    del GROUP_GAME_PROCESS[group.id]
                    await safeSendGroupMessage(
                        group, MessageChain.create("由于您是房主，本场房间已解散")
                    )
                    return False
                elif waiter1_member.id in GROUP_GAME_PROCESS[group.id]["members"]:
                    GROUP_GAME_PROCESS[group.id]["members"].remove(waiter1_member.id)
                    player_list = GROUP_GAME_PROCESS[group.id]["members"]
                    player_count = len(player_list)
                    if 6 > player_count > 1:
                        GROUP_GAME_PROCESS[group.id]["status"] = "pre_start"
                    else:
                        GROUP_GAME_PROCESS[group.id]["status"] = "waiting"
                    await safeSendGroupMessage(
                        group,
                        MessageChain.create(
                            At(waiter1_member.id),
                            Plain(f" 你已退出本轮游戏，当前共有 {player_count} / 6 人参与"),
                        ),
                    )
                else:
                    await safeSendGroupMessage(
                        group, MessageChain.create("你未参与本场游戏，无法退出")
                    )
            elif waiter1_message.asDisplay() == "提前开始":
                if waiter1_member.id == member.id:
                    if GROUP_GAME_PROCESS[group.id]["status"] == "pre_start":
                        await safeSendGroupMessage(
                            group,
                            MessageChain.create(
                                At(waiter1_member.id),
                                Plain(" 已强制开始本场游戏"),
                            ),
                        )
                        GROUP_GAME_PROCESS[group.id]["status"] = "running"
                        return True
                    else:
                        await safeSendGroupMessage(
                            group,
                            MessageChain.create(
                                At(waiter1_member.id),
                                Plain(" 当前游戏人数不足，无法强制开始"),
                            ),
                        )
                else:
                    await safeSendGroupMessage(
                        group,
                        MessageChain.create(
                            At(waiter1_member.id),
                            Plain(" 你不是本轮游戏的发起者，无法强制开始本场游戏"),
                        ),
                    )

    if group.id in GROUP_RUNING_LIST:
        if GROUP_GAME_PROCESS[group.id]["status"] != "running":
            return await safeSendGroupMessage(
                group,
                MessageChain.create(
                    At(member.id),
                    " 本轮游戏已经开始，请等待其他人结束后再开始新的一局",
                ),
            )
        else:
            return await safeSendGroupMessage(
                group, MessageChain.create(At(member.id), " 本群的游戏还未开始，请输入“加入赛马”参与游戏")
            )
    elif member.id in MEMBER_RUNING_LIST:
        return await safeSendGroupMessage(
            group, MessageChain.create(" 你已经参与了其他群的游戏，请等待游戏结束")
        )

    if await reduce_gold(str(member.id), 5):
        MEMBER_RUNING_LIST.append(member.id)
        GROUP_RUNING_LIST.append(group.id)
        GROUP_GAME_PROCESS[group.id] = {
            "status": "waiting",
            "members": [member.id],
        }
        await safeSendGroupMessage(
            group, MessageChain.create("赛马小游戏开启成功，正在等待其他群成员加入，发送“加入赛马”参与游戏")
        )
    else:
        return await safeSendGroupMessage(
            group, MessageChain.create(f"你的{COIN_NAME}不足，无法开始游戏")
        )

    try:
        result = await asyncio.wait_for(inc.wait(waiter1), timeout=120)
        if result:
            GROUP_GAME_PROCESS[group.id]["status"] = "running"
        else:
            return

    except asyncio.TimeoutError:
        for player in GROUP_GAME_PROCESS[group.id]["members"]:
            await add_gold(str(player), 5)
        MEMBER_RUNING_LIST.remove(member.id)
        GROUP_RUNING_LIST.remove(group.id)
        del GROUP_GAME_PROCESS[group.id]
        return await safeSendGroupMessage(group, MessageChain.create("等待玩家加入超时，请重新开始"))

    await asyncio.sleep(2)
    # 开始游戏
    player_list = GROUP_GAME_PROCESS[group.id]["members"]
    random.shuffle(player_list)
    game_data = {
        "player": {
            player: {
                "horse": i,
                "score": 0,
                "name": (await app.getMember(group.id, player)).name,
            }
            for i, player in enumerate(player_list, 1)
        },
        "winer": None,
    }
    game_image = await asyncio.to_thread(draw_game, game_data)
    await safeSendGroupMessage(
        group,
        MessageChain.create(Image(data_bytes=game_image)),
    )

    while True:
        await asyncio.sleep(2)
        game_data = run_game(game_data.copy())
        print(game_data)
        winer = [
            player
            for player, data in game_data["player"].items()
            if data["score"] >= 100
        ]
        if winer:
            if len(winer) != 1:
                winer = sorted(
                    game_data["player"].items(),
                    key=lambda x: x[1]["score"],
                    reverse=True,
                )[0][0]
                game_data["winer"] = winer
            else:
                game_data["winer"] = winer[0]
            break
        else:
            game_image = await asyncio.to_thread(draw_game, game_data)
            await safeSendGroupMessage(
                group,
                MessageChain.create(Image(data_bytes=game_image)),
            )

    # 结束游戏
    for player, data in game_data["player"].items():
        if data["score"] >= 100:
            game_data["player"][player].update({"score": 102})
    game_image = await asyncio.to_thread(draw_game, game_data)
    await safeSendGroupMessage(
        group,
        MessageChain.create(Image(data_bytes=game_image)),
    )
    player_count = len(game_data["player"])
    gold_count = (player_count * 5) - player_count
    await asyncio.sleep(1)
    await safeSendGroupMessage(
        group,
        MessageChain.create(
            "游戏结束，获胜者是：",
            At(game_data["winer"]),
            f"已获得 {gold_count} {COIN_NAME}",
        ),
    )
    await add_gold(str(game_data["winer"]), gold_count)
    MEMBER_RUNING_LIST.remove(member.id)
    GROUP_RUNING_LIST.remove(group.id)
    del GROUP_GAME_PROCESS[group.id]


@channel.use(ListenerSchema(listening_events=[ApplicationShutdowned]))
async def groupDataInit():
    for game_group in GROUP_RUNING_LIST:
        if game_group in GROUP_GAME_PROCESS:
            for player in GROUP_GAME_PROCESS[game_group]["members"]:
                await add_gold(str(player), 5)
            await safeSendGroupMessage(
                game_group,
                MessageChain.create(
                    [
                        Plain(
                            f"由于 {yaml_data['Basic']['BotName']} 正在重启，本场赛马重置，已补偿所有玩家5个{COIN_NAME}"
                        )
                    ]
                ),
            )
