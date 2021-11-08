import time
import httpx

from pathlib import Path
from graia.saya import Saya, Channel
from graia.ariadne.model import Group, Member
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import GroupMessage
from graia.broadcast.interrupt import InterruptControl
from graia.ariadne.message.element import Image, Plain, At, Source
from graia.ariadne.message.parser.pattern import RegexMatch
from graia.ariadne.message.parser.literature import Literature
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import Twilight, Sparkle

from config import yaml_data, group_data
from util.text2image import create_image
from util.control import Permission, Interval
from util.TextModeration import text_moderation
from util.ImageModeration import image_moderation
from util.sendMessage import safeSendGroupMessage

from .db import throw_bottle, get_bottle, clear_bottle, count_bottle, delete_bottle, get_bottle_by_id

saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
inc = InterruptControl(bcc)

IMAGE_PATH = Path(__file__).parent.joinpath('image')
IMAGE_PATH.mkdir(exist_ok=True)


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Literature("丢漂流瓶")],
                            decorators=[Permission.require(), Interval.require(600)]))
async def throw_bottle_handler(group: Group, member: Member, message: MessageChain, source: Source):

    if yaml_data['Saya']['DriftingBottle']['Disabled']:
        return
    elif 'DriftingBottle' in group_data[str(group.id)]['DisabledFunc']:
        return

    saying = message.asDisplay().split(" ", 1)

    if len(saying) == 1:
        return await safeSendGroupMessage(group, MessageChain.create("丢漂流瓶的话，请加上漂流瓶的内容！"))
    else:
        text = None
        image_name = None
        if message.has(Plain):
            text = MessageChain.create(message.get(Plain)).merge(True).asDisplay()[4:].strip()
            if text:
                if "magnet:" in text:
                    return await safeSendGroupMessage(group, MessageChain.create("您？"))
                moderation = await text_moderation(text)
                if moderation["Suggestion"] != "Pass":
                    return await safeSendGroupMessage(group, MessageChain.create("你的漂流瓶内包含违规内容，请检查后重新丢漂流瓶！"))
            elif text_len := len(text) > 400:
                return await safeSendGroupMessage(group, MessageChain.create(f"你的漂流瓶内容过长（{text_len} / 400）！"))

        if message.has(Image):
            if len(message.get(Image)) > 1:
                return await safeSendGroupMessage(group, MessageChain.create("丢漂流瓶的话，只能携带一张图片哦！"))
            else:
                image_url = message.getFirst(Image).url
                moderation = await image_moderation(image_url)
                if moderation["Suggestion"] != "Pass":
                    return await safeSendGroupMessage(group, MessageChain.create("你的漂流瓶包含违规内容，请检查后重新丢漂流瓶！"))
                async with httpx.AsyncClient() as client:
                    resp = await client.get(image_url)
                    image_type = resp.headers['Content-Type']
                    image = resp.content
                image_name = str(time.time()) + "." + image_type.split("/")[1]
                IMAGE_PATH.joinpath(image_name).write_bytes(image)

        if text is None and image_name is None:
            return await safeSendGroupMessage(group, MessageChain.create("丢漂流瓶的话，请加上漂流瓶的内容！"))

        bottle = throw_bottle(member, text, image_name)
        await safeSendGroupMessage(group, MessageChain.create([
            At(member.id), Plain(f" 丢出了一个漂流瓶！\n瓶子编号为：{bottle}")
        ]), quote=source)


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Twilight(Sparkle([RegexMatch(r"[捞|捡]漂流瓶")]))],
                            decorators=[Permission.require(), Interval.require(30)]))
async def pick_bottle_handler(group: Group):

    if yaml_data['Saya']['DriftingBottle']['Disabled']:
        return
    elif 'DriftingBottle' in group_data[str(group.id)]['DisabledFunc']:
        return

    bottle = get_bottle()

    if bottle is None:
        return await safeSendGroupMessage(group, MessageChain.create("没有漂流瓶可以捡哦！"))
    else:
        times = bottle['fishing_times']
        times_msg = "捡到的漂流瓶已经被捞了" + str(times) + "次" if times > 0 else "捡到的漂流瓶还没有被捞到过"
        msg = [Plain(f"你捡到了一个漂流瓶！\n瓶子编号为：{bottle['id']}\n{times_msg}\n"
                     #  f"漂流瓶来自 {bottle['group']} 群的 {bottle['member']}\n"
                     "漂流瓶内容为：\n")]
        if bottle['text'] is not None:
            image = await create_image(bottle['text'])
            msg.append(Image(data_bytes=image))
        if bottle['image'] is not None:
            msg.append(Image(path=IMAGE_PATH.joinpath(bottle['image'])))
        await safeSendGroupMessage(group, MessageChain.create(msg))


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Literature("清空漂流瓶")],
                            decorators=[Permission.require(Permission.MASTER), Interval.require()]))
async def clear_bottle_handler(group: Group):

    clear_bottle()
    await safeSendGroupMessage(group, MessageChain.create("漂流瓶已经清空！"))


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Literature("漂流瓶")],
                            decorators=[Permission.require(), Interval.require()]))
async def drifting_bottle_handler(group: Group):

    if yaml_data['Saya']['DriftingBottle']['Disabled']:
        return
    elif 'DriftingBottle' in group_data[str(group.id)]['DisabledFunc']:
        return

    count = count_bottle()
    msg = f"目前有 {count} 个漂流瓶在漂流" if count > 0 else "目前没有漂流瓶在漂流"
    msg += "\n漂流瓶可以使用“捞漂流瓶”命令捞到，也可以使用“丢漂流瓶”命令丢出”"

    await safeSendGroupMessage(group, MessageChain.create([Plain(msg)]))


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Literature("删漂流瓶")],
                            decorators=[Permission.require(Permission.MASTER)]))
async def delete_bottle_handler(group: Group, message: MessageChain):

    saying = message.asDisplay().split(" ", 1)

    if len(saying) == 1:
        return await safeSendGroupMessage(group, MessageChain.create("请输入要删除的漂流瓶编号！"))

    bottle_id = int(saying[1])
    bottle = get_bottle_by_id(bottle_id)
    if not bottle:
        return await safeSendGroupMessage(group, MessageChain.create("没有这个漂流瓶！"))

    delete_bottle(bottle_id)
    await safeSendGroupMessage(group, MessageChain.create("漂流瓶已经删除！"))


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Literature("查漂流瓶")],
                            decorators=[Permission.require(Permission.MASTER)]))
async def search_bottle_handler(group: Group, message: MessageChain):

    saying = message.asDisplay().split(" ", 1)

    if len(saying) == 1:
        return await safeSendGroupMessage(group, MessageChain.create("请输入要查找的漂流瓶编号！"))

    bottle_id = int(saying[1])
    bottle = get_bottle_by_id(bottle_id)
    if not bottle:
        return await safeSendGroupMessage(group, MessageChain.create("没有这个漂流瓶！"))

    bottle = bottle[0]
    msg = [Plain(f"漂流瓶编号为：{bottle.id}\n"
                 f"漂流瓶来自 {bottle.group} 群的 {bottle.member}\n")]
    if bottle.text is not None:
        image = await create_image(bottle.text)
        msg.append(Image(data_bytes=image))
    if bottle.image is not None:
        msg.append(Image(path=IMAGE_PATH.joinpath(bottle.image)))
    await safeSendGroupMessage(group, MessageChain.create(msg))
