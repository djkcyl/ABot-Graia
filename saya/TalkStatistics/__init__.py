import httpx
import datetime

from pathlib import Path
from loguru import logger
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group, Member
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.parser.literature import Literature
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.element import FlashImage, Image, Plain, Voice

from util.control import Permission
from util.sendMessage import selfSendGroupMessage
from database.usertalk import get_message_analysis, add_talk, archive_exists

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
                            decorators=[Permission.require(Permission.MASTER)]))
async def get_image(app: Ariadne, group: Group):

    talk_num, time = await get_message_analysis()
    talk_num.reverse()
    time.reverse()
    image = await get_mapping(talk_num, time)

    await selfSendGroupMessage(group, MessageChain.create([Image(data_bytes=image)]))


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            decorators=[Permission.require()]))
async def add_talk_word(app: Ariadne, group: Group, member: Member, message: MessageChain):
    if message.has(Plain):
        plain_list = message.get(Plain)
        plain = MessageChain.create(plain_list).asDisplay()
        await add_talk(str(member.id), str(group.id), 1, plain)
    elif message.has(Image):
        image_list = message.get(Image)
        for image in image_list:
            await download(app, image.url, image.id, "image", 2)
            await add_talk(str(member.id), str(group.id), 2, image.id, image.url)
    elif message.has(FlashImage):
        flash_image = message.getFirst(FlashImage)
        await download(app, flash_image.url, flash_image.id, "flashimage", 3)
        await add_talk(str(member.id), str(group.id), 3, flash_image.id, flash_image.url)
    elif message.has(Voice):
        voice = message.getFirst(Voice)
        await download(app, voice.url, voice.id, "voice", 4)
        await add_talk(str(member.id), str(group.id), 4, voice.id, voice.url)


async def download(url, name, path, type):
    now_time = datetime.datetime.now()
    now_path = data_path.joinpath(path, str(now_time.year), str(now_time.month), str(now_time.day))
    now_path.mkdir(0o775, True, True)
    if not await archive_exists(name, type):
        async with httpx.AsyncClient() as client:
            r = await client.get(url)
            now_path.joinpath(name).write_bytes(r.content)
    else:
        logger.info(f"已存在的文件 - {name}")
