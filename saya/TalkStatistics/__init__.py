import httpx
import datetime

from pathlib import Path
from graia.saya import Saya, Channel
from graia.application.group import Group, Member
from graia.application import GraiaMiraiApplication
from graia.application.event.messages import GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.parser.literature import Literature
from graia.application.message.elements.internal import FlashImage, Image, Image_UnsafeBytes, MessageChain, Plain, Voice

from util.limit import member_limit_check
from util.UserBlock import group_black_list_block
from datebase.usertalk import get_message_analysis, add_talk

from .mapping import get_mapping

saya = Saya.current()
channel = Channel.current()
data_path = Path("archive")

if not data_path.exists():
    print("存档目录不存在，正在创建")
    data_path.mkdir()
    image = data_path.joinpath("image").mkdir()
    flashimage = data_path.joinpath("flashimage").mkdir()
    voice = data_path.joinpath("voice").mkdir()


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Literature("查看消息量统计")],
                            headless_decorators=[member_limit_check(15), group_black_list_block()]))
async def get_image(app: GraiaMiraiApplication, group: Group):

    talk_num, time = await get_message_analysis()
    talk_num.reverse()
    time.reverse()
    image = await get_mapping(talk_num, time)

    await app.sendGroupMessage(group, MessageChain.create([Image_UnsafeBytes(image.getvalue())]))


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            headless_decorators=[group_black_list_block()]))
async def add_talk_word(app: GraiaMiraiApplication, group: Group, member: Member, message: MessageChain):
    if message.has(Plain):
        plain_list = message.get(Plain)
        plain = MessageChain.create(plain_list).asDisplay()
        await add_talk(str(member.id), str(group.id), 1, plain)
    elif message.has(Image):
        image_list = message.get(Image)
        for image in image_list:
            await download(app, image.url, image.imageId, "image")
            await add_talk(str(member.id), str(group.id), 2, image.imageId, image.url)
    elif message.has(FlashImage):
        flash_image = message.getFirst(FlashImage)
        await download(app, flash_image.url, flash_image.imageId, "flashimage")
        await add_talk(str(member.id), str(group.id), 3, flash_image.imageId, flash_image.url)
    elif message.has(Voice):
        voice = message.getFirst(Voice)
        await download(app, voice.url, voice.imageId, "voice")
        await add_talk(str(member.id), str(group.id), 4, voice.voiceId, voice.url)


async def download(app: GraiaMiraiApplication, url, name, path):
    now_time = datetime.datetime.now()
    now_path = data_path.joinpath(path, str(now_time.year), str(now_time.month))
    now_path.mkdir(0o775, True, True)
    if not now_path.joinpath(name).exists():
        async with httpx.AsyncClient() as client:
            r = await client.get(url)
            now_path.joinpath(name).write_bytes(r.content)
    else:
        app.logger.info(f"已存在的文件 - {name}")
