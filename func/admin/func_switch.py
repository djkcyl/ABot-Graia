from typing import Annotated

from avilla.core import Context, Message, MessageReceived
from avilla.twilight.twilight import (
    ArgResult,
    ArgumentMatch,
    FullMatch,
    RegexMatch,
    ResultValue,
    SpacePolicy,
    Twilight,
    WildcardMatch,
)
from graia.amnesia.message.chain import MessageChain
from graia.saya import Channel, Saya
from graiax.shortcut import decorate, dispatch, listen

from utils.message.parse.twilight.preprocessor import MentionMe
from utils.saya import build_metadata
from utils.saya.model import AGroupModel, FuncItem, FuncType

channel = Channel.current()
channel.meta = build_metadata(
    func_type=FuncType.admin,
    name="功能开关",
    version="1.0",
    description="打开或关闭某个功能",
    usage=["发送指令：[开启/关闭] 功能 <id> [-a, --all]"],
    options=[
        {"name": "action", "help": "要执行的操作，可选：开启/关闭"},
        {"name": "id", "help": "功能的id，指定要开启/关闭的功能，可多选（空格分隔）"},
        {"name": "-a, --all", "help": "是否一键开启/关闭所有功能，可选"},
    ],
    example=[
        {"run": "开启 功能 1", "to": "开启第一个功能"},
        {"run": "关闭 功能 1 2 3", "to": "关闭第1、2、3个功能"},
        {"run": "开启 功能 --all", "to": "开启所有功能"},
    ],
    can_be_disabled=False,
)
saya = Saya.current()


@listen(MessageReceived)
@dispatch(
    Twilight(
        "action" @ RegexMatch(r"/(开启|关闭)").param(SpacePolicy.NOSPACE),
        FullMatch("功能"),
        "arg_all" @ ArgumentMatch("-a", "--all", action="store_true"),
        "arg_func_ids" @ WildcardMatch(),
        preprocessor=MentionMe(),
    ),
)
async def main(
    ctx: Context,
    group_data: AGroupModel,
    action: Annotated[MessageChain, ResultValue()],
    arg_all: ArgResult,
    arg_func_ids: Annotated[MessageChain, ResultValue()],
):
    # 获取所有功能列表
    func_list = [
        (func_id, FuncItem(**channel.meta)) for func_id, channel in saya.channels.items() if not channel.meta["hidden"]
    ]
    # 对功能列表进行排序
    func_list.sort(key=lambda x: (x[1].func_type, x[0]))

    # 定义一个列表，用于存储需要开启或关闭的功能
    need_change: list[tuple[str, FuncItem]] = []

    # 如果指定了一键开启或关闭所有功能
    if arg_all.result:
        print("all", arg_all, bool(arg_all))
        need_change = func_list
    else:
        # 获取指定的功能id列表
        func_id_list = str(arg_func_ids).split()
        for func_id in func_id_list:
            # 在功能列表中查找指定的功能
            func, meta = await find_function(func_list, func_id)

            # 如果找不到指定的功能，则返回错误信息
            if not func or not meta:
                await ctx.scene.send_message("输入的功能不存在，无法开启/关闭")
                return

            # 如果指定的功能正在维护，则返回错误信息
            if meta.maintain and not meta.can_be_disabled:
                await ctx.scene.send_message("输入的功能正在维护或为必要功能，无法开启/关闭")
                return
            else:
                need_change.append((func, meta))

    # 定义计数器，用于统计开启或关闭功能的结果
    action_success = 0
    action_fail = 0

    # 定义一个字典，用于将操作类型转换为对应的函数
    action_to_function = {"开启": group_data.enable_function, "关闭": group_data.disable_function}
    function = action_to_function[str(action)]

    # 遍历需要开启或关闭的功能列表
    for func, meta in need_change:
        # 调用对应的函数，开启或关闭功能
        if await function(func, meta):
            action_success += 1
        else:
            action_fail += 1

    # 发送操作结果
    await ctx.scene.send_message(
        f"功能{str(action)}完成，共{len(need_change)}个功能，成功{action_success}个，失败{action_fail}个",
    )


async def find_function(func_list: list[tuple[str, FuncItem]], func_want: str):
    """
    在功能列表中查找指定功能。

    参数:
        func_list: 功能列表
        func_want: 指定的功能名称或ID

    返回值:
        如果找到指定功能，则返回该功能的名称和元数据；否则返回None。
    """
    try:
        # 先按照名称查找
        return next(filter(lambda x: x[1].name == func_want, func_list))
    except StopIteration:
        try:
            # 如果找不到，则按照ID查找
            return func_list[int(func_want) - 1]
        except (IndexError, ValueError):
            return None, None
