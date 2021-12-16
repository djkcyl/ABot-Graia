import re
import asyncio

from graia.saya import Saya, Channel
from graia.ariadne.model import Group
from graia.ariadne.message.element import Source
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import Twilight, FullMatch, WildcardMatch

from config import yaml_data, group_data
from util.control import Permission, Interval
from util.sendMessage import safeSendGroupMessage


saya = Saya.current()
channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                {
                    "head": FullMatch("计算器"),
                    "formula": WildcardMatch(optional=True),
                }
            )
        ],
        decorators=[Permission.require(), Interval.require()],
    )
)
async def calculator_main(group: Group, formula: WildcardMatch, source: Source):

    if (
        yaml_data["Saya"]["Calculator"]["Disabled"]
        and group.id != yaml_data["Basic"]["Permission"]["DebugGroup"]
    ):
        return
    elif "Calculator" in group_data[str(group.id)]["DisabledFunc"]:
        return

    if formula.matched:
        expression = rep_str(formula.result.asDisplay())
        if len(expression) > 800:
            return await safeSendGroupMessage(
                group, MessageChain.create("字符数过多"), quote=source.id
            )
        try:
            answer = await asyncio.wait_for(
                asyncio.to_thread(arithmetic, expression), timeout=15
            )
        except ZeroDivisionError:
            return await safeSendGroupMessage(
                group, MessageChain.create("0 不可作为除数"), quote=source.id
            )
        except asyncio.TimeoutError:
            return await safeSendGroupMessage(
                group, MessageChain.create("计算超时"), quote=source.id
            )
        except Exception:
            return await safeSendGroupMessage(
                group, MessageChain.create("出现未知错误，终止计算"), quote=source.id
            )

        await safeSendGroupMessage(group, MessageChain.create(answer), quote=source.id)


def rep_str(say: str):
    rep_list = [
        [[" "], ""],
        [["加", "＋"], "+"],
        [["减", "－"], "-"],
        [["乘", "x", "X", "×"], "*"],
        [["除", "÷", "∣"], "/"],
        [["（"], "("],
        [["）"], ")"],
    ]
    for rp in rep_list:
        for old_str in rp[0]:
            say = say.replace(old_str, rp[1])
    return say


def arithmetic(expression="1+1"):
    content = re.search(r"\(([-+*/]*\d+\.?\d*)+\)", expression)
    if content:
        content = content.group()
        content = content[1:-1]
        replace_content = next_arithmetic(content)
        expression = re.sub(
            r"\(([-+*/]*\d+\.?\d*)+\)", replace_content, expression, count=1
        )
    else:
        answer = next_arithmetic(expression)
        return answer
    return arithmetic(expression)


def next_arithmetic(content):
    while True:
        next_content_mul_div = re.search(r"\d+\.?\d*[*/][-+]?\d+\.?\d*", content)
        if next_content_mul_div:
            next_content_mul_div = next_content_mul_div.group()
            mul_div_content = mul_div(next_content_mul_div)
            content = re.sub(
                r"\d+\.?\d*[*/][-+]?\d+\.?\d*", str(mul_div_content), content, count=1
            )
            continue
        next_content_add_sub = re.search(r"-?\d+\.?\d*[-+][-+]?\d+\.?\d*", content)
        if next_content_add_sub:
            next_content_add_sub = next_content_add_sub.group()
            add_sub_content = add_sub(next_content_add_sub)
            add_sub_content = str(add_sub_content)
            content = re.sub(
                r"-?\d+\.?\d*[-+]-?\d+\.?\d*", str(add_sub_content), content, count=1
            )
            continue
        else:
            break
    return content


def add_sub(content):
    if "+" in content:
        content = content.split("+")
        content = float(content[0]) + float(content[1])
        return content
    elif "-" in content:
        content = content.split("-")
        if content[0] == "-" and content[2] == "-":
            content = -float(content[1]) - float(content[-1])
            return content
        if content[0] == "-":
            content = -float(content[1]) - float(content[-1])
            return content
        if content[1] == "-" and content[2] == "-":
            content = -float(content[0]) + float(content[-1])
            return content
        if content[1] == "":
            content = float(content[0]) - float(content[2])
            return content
        if content[0] == "" and content[2] != "":
            content = -float(content[1]) - float(content[2])
            return content
        if content[0] == "" and content[2] == "":
            content = -float(content[1]) + float(content[3])
            return content
        else:
            content = float(content[0]) - float(content[1])
            return content


def mul_div(content):
    if "*" in content:
        content = content.split("*")
        content = float(content[0]) * float(content[1])
        return content
    elif "/" in content:
        content = content.split("/")
        content = float(content[0]) / float(content[1])
        return content
