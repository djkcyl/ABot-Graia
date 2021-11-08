import time
import httpx
import datetime

from pathlib import Path
from loguru import logger
from graiax import silkcoder
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group, Member
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.parser.literature import Literature
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.element import FlashImage, Image, Plain, Voice

from util.control import Permission
from util.sendMessage import safeSendGroupMessage
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

    await safeSendGroupMessage(group, MessageChain.create([Image(data_bytes=image)]))


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
            image_id = image.url.split('/')[5].split("-")[2]
            async with httpx.AsyncClient() as client:
                rep = await client.get(image.url)
            content_type = rep.headers["content-type"].split("/")[1]
            image_name = f"{image_id}.{content_type}"
            await download(image.url, image_name, "image", 2)
            await add_talk(str(member.id), str(group.id), 2, image_name, image.url)
    elif message.has(FlashImage):
        flash_image = message.getFirst(FlashImage)
        image_id = flash_image.url.split('/')[5].split("-")[2]
        async with httpx.AsyncClient() as client:
            rep = await client.get(flash_image.url)
        content_type = rep.headers["content-type"].split("/")[1]
        image_name = f"{image_id}.{content_type}"
        await download(flash_image.url, image_name, "flashimage", 3)
        await add_talk(str(member.id), str(group.id), 3, image_name, flash_image.url)
    elif message.has(Voice):
        voice = message.getFirst(Voice)
        voice_id = f"{member.id}-{int(time.time() * 100)}"
        await download(voice.url, voice_id, "voice", 4)
        await add_talk(str(member.id), str(group.id), 4, voice_id, voice.url)


async def download(url, name, path, type):
    now_time = datetime.datetime.now()
    now_path = data_path.joinpath(path, str(now_time.year), str(now_time.month), str(now_time.day))
    now_path.mkdir(0o775, True, True)
    if not await archive_exists(name, type):
        async with httpx.AsyncClient() as client:
            r = await client.get(url)
            if type == 4:
                f = await silkcoder.decode(r.content, audio_format="mp3")
            else:
                f = r.content
            now_path.joinpath(f"{name}.mp3").write_bytes(f)
    else:
        logger.info(f"已存在的文件 - {name}")
