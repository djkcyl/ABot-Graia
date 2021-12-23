import time
import json

from pathlib import Path
from graia.saya import Saya, Channel
from graia.ariadne.model import Group
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.element import At, Plain, Image
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    RegexMatch,
    WildcardMatch,
)

from util.text2image import create_image
from util.control import Permission, Interval
from util.sendMessage import safeSendGroupMessage
from config import save_config, yaml_data, group_data, COIN_NAME

saya = Saya.current()
channel = Channel.current()

data = json.loads(
    Path(__file__)
    .parent.joinpath("func.json")
    .read_text(encoding="utf-8")
    .replace("$COIN_NAME", COIN_NAME)
)
funcList = data["funcList"]
funcHelp = data["funcHelp"]
configList = data["configList"]

DisabledFunc = []
for func in funcList:
    if func["default_disabled"]:
        DisabledFunc.append(func["key"])

groupInitData = {
    "DisabledFunc": DisabledFunc,
    "EventBroadcast": {"Enabled": True, "Message": None},
}


@channel.use(
    ListenerSchema(listening_events=[GroupMessage], decorators=[Permission.require()])
)
async def atrep(group: Group, message: MessageChain):
    if At(yaml_data["Basic"]["MAH"]["BotQQ"]) in message and (
        MessageChain.create(message.get(Plain)).asDisplay() == " "
        if message.get(Plain)
        else True
    ):
        now_localtime = time.strftime("%H:%M:%S", time.localtime())
        if "00:00:00" < now_localtime < "07:30:00":
            msg = Plain("Zzzzzz~")
        else:
            image = await create_image(
                str(
                    f"我是{yaml_data['Basic']['Permission']['MasterName']}"
                    + f"的机器人{yaml_data['Basic']['BotName']}"
                    + f"\n如果有需要可以联系主人QQ”{str(yaml_data['Basic']['Permission']['Master'])}“，"
                    + f"\n邀请 {yaml_data['Basic']['BotName']} 加入其他群需先询问主人获得白名单"
                    + f"\n{yaml_data['Basic']['BotName']} 被群禁言后会自动退出该群。"
                    + "\n发送 <菜单> 可以查看功能列表"
                    + "\n@不会触发任何功能　　　　@不会触发任何功能"
                    + "\n@不会触发任何功能　　　　@不会触发任何功能"
                    + "\n@不会触发任何功能　　　　@不会触发任何功能"
                    + "\n@不会触发任何功能　　　　@不会触发任何功能"
                    + "\n@不会触发任何功能　　　　@不会触发任何功能"
                    + "\n@不会触发任何功能　　　　@不会触发任何功能"
                )
            )
            msg = Image(data_bytes=image)
        await safeSendGroupMessage(group, MessageChain.create([msg]))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight([FullMatch("功能")], {"func": WildcardMatch()})],
        decorators=[Permission.require(), Interval.require(5)],
    )
)
async def funchelp(group: Group, func: WildcardMatch):
    if func.matched:
        num = func.result.asDisplay().strip()
        if num.isdigit():
            func_id = int(num) - 1
            if func_id >= len(funcList):
                return await safeSendGroupMessage(
                    group,
                    MessageChain.create("没有这个功能，请输入菜单查看所有功能"),
                )
        elif num in funcHelp:
            func_id = [*funcHelp].index(num)
        else:
            return await safeSendGroupMessage(
                group, MessageChain.create([Plain("功能编号仅可为数字或其对应的功能名")])
            )
        sayfunc = funcList[func_id]["name"]
        funckey = funcList[func_id]["key"]
        funcGlobalDisabled = yaml_data["Saya"][funckey]["Disabled"]
        funcGroupDisabledList = funckey in group_data[str(group.id)]["DisabledFunc"]
        if funcGlobalDisabled or funcGroupDisabledList:
            return await safeSendGroupMessage(
                group, MessageChain.create([Plain("该功能暂不开启")])
            )
        help = str(
            sayfunc
            + f"\n\n{funcHelp[sayfunc]['instruction']}"
            + "\n \n>>> 用法 >>>\n"
            + funcHelp[sayfunc]["usage"]
            + "\n \n>>> 注意事项 >>>\n"
            + funcHelp[sayfunc]["options"]
            + "\n \n>>> 示例 >>>\n"
            + funcHelp[sayfunc]["example"]
        )
        image = await create_image(help)
        await safeSendGroupMessage(
            group, MessageChain.create([Image(data_bytes=image)])
        )
    else:
        await safeSendGroupMessage(group, MessageChain.create([Plain("请输入功能编号")]))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight({"head": RegexMatch(r"^[。\./]?help$|^帮助$|^菜单$")})],
        decorators=[Permission.require()],
    )
)
async def help(group: Group):
    msg = (
        f"{yaml_data['Basic']['BotName']} 群菜单 / {str(group.id)}\n{group.name}\n"
        + "========================================================"
    )
    i = 1
    for func in funcList:
        funcname = func["name"]
        funckey = func["key"]
        funcGlobalDisabled = yaml_data["Saya"][funckey]["Disabled"]
        funcGroupDisabledList = func["key"] in group_data[str(group.id)]["DisabledFunc"]
        if funcGlobalDisabled:
            statu = "【全局关闭】"
        elif funcGroupDisabledList:
            statu = "【  关闭  】"
        else:
            statu = "            "
        if i < 10:
            si = " " + str(i)
        else:
            si = str(i)
        msg += f"\n{si}  {statu}  {funcname}"
        i += 1
    msg += str(
        "\n========================================================"
        + "\n详细查看功能使用方法请发送 功能 <id>，例如：功能 1"
        + "\n管理员可发送 开启功能/关闭功能 <功能id> "
        + "\n每日00:00至07:30为休息时间，将关闭部分功能"
        + "\n所有功能均无需@机器人本身"
        + "\n源码：github.com/djkcyl/ABot-Graia"
        + f"\n更多功能待开发，如有特殊需求可以向 {yaml_data['Basic']['Permission']['Master']} 询问"
    )
    image = await create_image(msg, 80)
    await safeSendGroupMessage(group, MessageChain.create([Image(data_bytes=image)]))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight({"head": FullMatch("开启功能"), "func": WildcardMatch(optional=True)})
        ],
        decorators=[Permission.require(Permission.GROUP_ADMIN), Interval.require(5)],
    )
)
async def on_func(group: Group, func: WildcardMatch):
    if func.matched:
        say = func.result.asDisplay().strip()
        if say.isdigit():
            sayfunc = int(say) - 1
            try:
                func = funcList[sayfunc]
            except IndexError:
                await safeSendGroupMessage(
                    group, MessageChain.create([Plain("该功能编号不存在")])
                )
            else:
                funcname = func["name"]
                funckey = func["key"]
                funcGlobalDisabled = yaml_data["Saya"][funckey]["Disabled"]
                funcGroupDisabled = (
                    func["key"] in group_data[str(group.id)]["DisabledFunc"]
                )
                funcDisabledList = group_data[str(group.id)]["DisabledFunc"]
                if funcGlobalDisabled:
                    await safeSendGroupMessage(
                        group, MessageChain.create([Plain(f"{funcname} 当前处于全局禁用状态")])
                    )
                elif funcGroupDisabled:
                    funcDisabledList.remove(funckey)
                    group_data[str(group.id)]["DisabledFunc"] = funcDisabledList
                    save_config()
                    await safeSendGroupMessage(
                        group, MessageChain.create(f"{funcname} 已开启")
                    )
                else:
                    await safeSendGroupMessage(
                        group, MessageChain.create(f"{funcname} 已处于开启状态")
                    )
        else:
            await safeSendGroupMessage(group, MessageChain.create("功能编号仅可为数字"))
    else:
        await safeSendGroupMessage(group, MessageChain.create("请输入功能编号"))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight({"head": FullMatch("关闭功能"), "func": WildcardMatch(optional=True)})
        ],
        decorators=[Permission.require(Permission.GROUP_ADMIN), Interval.require(5)],
    )
)
async def off_func(group: Group, func: WildcardMatch):
    if func.matched:
        say = func.result.asDisplay().strip()
        if say.isdigit():
            sayfunc = int(say) - 1
            try:
                func = funcList[sayfunc]
            except IndexError:
                await safeSendGroupMessage(
                    group, MessageChain.create([Plain("该功能编号不存在")])
                )
            else:
                funcname = func["name"]
                funckey = func["key"]
                funcCanDisabled = func["can_disabled"]
                funcDisabledList = group_data[str(group.id)]["DisabledFunc"]
                funcGroupDisabled = func["key"] in funcDisabledList
                if not funcCanDisabled:
                    await safeSendGroupMessage(
                        group, MessageChain.create([Plain(f"{funcname} 无法被关闭")])
                    )
                elif not funcGroupDisabled:
                    funcDisabledList.append(funckey)
                    group_data[str(group.id)]["DisabledFunc"] = funcDisabledList
                    save_config()
                    await safeSendGroupMessage(
                        group, MessageChain.create([Plain(f"{funcname} 已关闭")])
                    )
                else:
                    await safeSendGroupMessage(
                        group, MessageChain.create([Plain(f"{funcname} 已处于关闭状态")])
                    )
        else:
            await safeSendGroupMessage(group, MessageChain.create("功能编号仅可为数字"))
    else:
        await safeSendGroupMessage(group, MessageChain.create("请输入功能编号"))


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [FullMatch("群功能")],
                {
                    "reg1": RegexMatch("修改|查看|关闭|开启", optional=True),
                    "reg2": RegexMatch(
                        "|".join(x["name"] for x in configList), optional=True
                    ),
                    "reg3": WildcardMatch(optional=True),
                },
            )
        ],
        decorators=[Permission.require(Permission.GROUP_ADMIN), Interval.require(5)],
    )
)
async def group_func(
    group: Group, reg1: RegexMatch, reg2: RegexMatch, reg3: WildcardMatch
):

    if reg1.matched:
        ctrl = reg1.result.getFirst(Plain).text
        if ctrl == "修改":
            if reg2.matched:
                configname = reg2.result.getFirst(Plain).text
                for config in configList:
                    if config["name"] == configname:
                        if config["can_edit"]:
                            if reg3.matched:
                                config_Message = reg3.result.getFirst(Plain).text
                                group_data[str(group.id)][config["key"]][
                                    "Message"
                                ] = config_Message
                                save_config()
                                return await safeSendGroupMessage(
                                    group,
                                    MessageChain.create(
                                        [Plain(f"{configname} 已修改为 {config_Message}")]
                                    ),
                                )
                            else:
                                return await safeSendGroupMessage(
                                    group, MessageChain.create([Plain("请输入修改后的值")])
                                )
                        else:
                            return await safeSendGroupMessage(
                                group,
                                MessageChain.create([Plain(f"{configname} 不可修改")]),
                            )
                else:
                    return await safeSendGroupMessage(
                        group, MessageChain.create([Plain(f"{configname} 不存在")])
                    )
            else:
                return await safeSendGroupMessage(
                    group, MessageChain.create([Plain("请输入需要修改的配置名称")])
                )
        elif ctrl == "查看":
            if reg2.matched:
                configname = reg2.result.getFirst(Plain).text
                for config in configList:
                    if config["name"] == configname:
                        config_Message = group_data[str(group.id)][config["key"]][
                            "Message"
                        ]
                        if config_Message:
                            return await safeSendGroupMessage(
                                group,
                                MessageChain.create(
                                    [Plain(f"{configname} 当前值为 {config_Message}")]
                                ),
                            )
                        else:
                            return await safeSendGroupMessage(
                                group,
                                MessageChain.create([Plain(f"{configname} 当前值为 空")]),
                            )
                else:
                    return await safeSendGroupMessage(
                        group, MessageChain.create([Plain(f"{configname} 不存在")])
                    )
            else:
                return await safeSendGroupMessage(
                    group, MessageChain.create([Plain("请输入需要查看的配置名称")])
                )
        elif ctrl == "关闭":
            if reg2.matched:
                configname = reg2.result.getFirst(Plain).text
                for config in configList:
                    if config["name"] == configname:
                        configkey = config["key"]
                        if group_data[str(group.id)][configkey]["Enabled"]:
                            group_data[str(group.id)][configkey]["Enabled"] = False
                            save_config()
                            return await safeSendGroupMessage(
                                group, MessageChain.create([Plain(f"{configname} 已关闭")])
                            )
                        else:
                            return await safeSendGroupMessage(
                                group,
                                MessageChain.create([Plain(f"{configname} 已处于关闭状态")]),
                            )
                else:
                    return await safeSendGroupMessage(
                        group, MessageChain.create([Plain(f"{configname} 不存在")])
                    )
            else:
                return await safeSendGroupMessage(
                    group, MessageChain.create([Plain("请输入需要关闭的配置名称")])
                )
        elif ctrl == "开启":
            if reg2.matched:
                configname = reg2.result.getFirst(Plain).text
                for config in configList:
                    if config["name"] == configname:
                        configkey = config["key"]
                        if not group_data[str(group.id)][configkey]["Enabled"]:
                            group_data[str(group.id)][configkey]["Enabled"] = True
                            save_config()
                            return await safeSendGroupMessage(
                                group, MessageChain.create([Plain(f"{configname} 已开启")])
                            )
                        else:
                            return await safeSendGroupMessage(
                                group,
                                MessageChain.create([Plain(f"{configname} 已处于开启状态")]),
                            )
                else:
                    return await safeSendGroupMessage(
                        group, MessageChain.create([Plain(f"{configname} 不存在")])
                    )
            else:
                return await safeSendGroupMessage(
                    group, MessageChain.create([Plain("请输入需要开启的配置名称")])
                )
        else:
            return await safeSendGroupMessage(
                group, MessageChain.create([Plain("请输入修改|查看|关闭|开启")])
            )
    else:
        msg = "当前可调整的群功能有："

        for config in configList:
            configname = config["name"]
            configkey = config["key"]
            configstatus = group_data[str(group.id)][configkey]["Enabled"]
            configstatus_str = "已开启" if configstatus else "已关闭"

            msg += f"\n{configname}    {configstatus_str}"

        msg += "\n如需修改请发送 群功能 <操作> <功能名>，例如：群功能 关闭 入群欢迎\n可用操作：修改、查看、关闭、开启"

        image = await create_image(msg, cut=80)
        return await safeSendGroupMessage(
            group, MessageChain.create([Image(data_bytes=image)])
        )
