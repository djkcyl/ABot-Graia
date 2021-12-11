import math
import hashlib
import zipfile
import asyncio

from io import BytesIO
from loguru import logger
from PIL import Image as IMG
from graia.saya import Saya, Channel
from multiprocessing import cpu_count
from graia.ariadne.model import Group, Member
from graia.broadcast.interrupt.waiter import Waiter
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import GroupMessage
from waifu2x_vulkan import waifu2x_vulkan as waifu2x
from graia.broadcast.interrupt import InterruptControl
from graia.ariadne.message.parser.twilight import Twilight
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.event.lifecycle import ApplicationShutdowned
from graia.ariadne.message.element import At, Image, Plain, Source
from graia.ariadne.message.parser.pattern import ElementMatch, FullMatch


from database.db import reduce_gold
from util.update_cos import UpdateCos
from util.TimeTool import TimeRecorder
from util.control import Permission, Interval
from util.QRGeneration import QRcode_generation
from util.sendMessage import safeSendGroupMessage
from config import yaml_data, group_data, COIN_NAME

saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
inc = InterruptControl(bcc)
sts = waifu2x.init()
gpuList = waifu2x.getGpuInfo()
cpu = math.ceil(cpu_count() / 2)


if "llvm" in gpuList[0].lower():
    waifu2x.initSet(-1, cpu)
    logger.info(f"not LLVM !!! - CPU Mode - {cpu}")
elif sts < 0:
    waifu2x.initSet(-0, cpu)
    logger.info(f"CPU Mode - {cpu}")
else:
    waifu2x.initSet(0, 1)
    logger.info("GPU Mode")


MEMBER_RUNING_LIST = []


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                {
                    "head": FullMatch("超分辨率"),
                    "enter": FullMatch("\n", optional=True),
                    "image": ElementMatch(Image, optional=True),
                }
            )
        ],
        decorators=[Permission.require(), Interval.require(120)],
    )
)
async def waifu2(
    member: Member,
    group: Group,
    image: ElementMatch,
    source: Source,
):

    if (
        yaml_data["Saya"]["Waifu2x"]["Disabled"]
        and group.id != yaml_data["Basic"]["Permission"]["DebugGroup"]
    ):
        return
    elif "Waifu2x" in group_data[str(group.id)]["DisabledFunc"]:
        return

    @Waiter.create_using_function([GroupMessage])
    async def image_waiter(
        waiter1_group: Group, waiter1_member: Member, waiter1_message: MessageChain
    ):
        if waiter1_group.id == group.id and waiter1_member.id == member.id:
            if waiter1_message.has(Image):
                return await waiter1_message.getFirst(Image).get_bytes()
            else:
                return False

    if member.id in MEMBER_RUNING_LIST:
        return
    else:
        MEMBER_RUNING_LIST.append(member.id)

    if image.matched:
        image_data = await image.result.get_bytes()
    else:
        await safeSendGroupMessage(
            group, MessageChain.create("请发送要处理的图片"), quote=source
        )
        try:
            image_data = await asyncio.wait_for(inc.wait(image_waiter), 30)
            if not image_data:
                return await safeSendGroupMessage(
                    group, MessageChain.create("你发送的不是“一张”图片，请重试"), quote=source
                )
        except asyncio.TimeoutError:
            MEMBER_RUNING_LIST.remove(member.id)
            return await safeSendGroupMessage(
                group, MessageChain.create("图片等待超时"), quote=source
            )

    img_x, img_y = IMG.open(BytesIO(image_data)).size
    size = img_x * img_y
    size_max = max(img_x, img_y)
    max_size = yaml_data["Saya"]["Waifu2x"]["MaxSize"]
    if size_max < 100:
        img_scale = 12
    elif 100 < size_max < 200:
        img_scale = 8
    elif 200 < size_max < 500:
        img_scale = 4
    else:
        img_scale = 2

    if size > max_size:
        MEMBER_RUNING_LIST.remove(member.id)
        return await safeSendGroupMessage(
            group, MessageChain.create(f"图片尺寸过大，暂不提供服务，请发送总像素小于 {max_size} 的图片")
        )

    if await reduce_gold(str(member.id), 10):
        await safeSendGroupMessage(group, MessageChain.create("正在处理，请稍候"), quote=source)
        time_recorder = TimeRecorder()
        waifu2x.add(
            image_data,
            waifu2x.MODEL_ANIME_STYLE_ART_RGB_NOISE3,
            1,
            scale=img_scale,
            tileSize=100,
        )
        newData, _, _, _ = await asyncio.to_thread(waifu2x.load, 0)
        img = IMG.open(BytesIO(newData))
        img.save(img_data := BytesIO(), format="PNG")

        if yaml_data["Saya"]["Waifu2x"]["UpdateCos"]:
            image_md5 = hashlib.md5(img_data.getvalue()).hexdigest()
            with zipfile.ZipFile(
                zip_bio := BytesIO(),
                "w",
                allowZip64=False,
                compression=zipfile.ZIP_DEFLATED,
            ) as zipFile:
                zipFile.writestr(
                    f"{image_md5}.png",
                    img_data.getvalue(),
                )
            cos = UpdateCos(zip_bio.getvalue(), f"Waifu2x/{image_md5}.zip")
            await cos.update()
            url = await cos.get_url()
            final_img = QRcode_generation(url)
            msg = MessageChain.create(
                Plain("请扫码二维码下载\n"),
                Image(data_bytes=final_img),
                Plain("\n本链接仅在 10 分钟内可用，请尽快保存。"),
            )
        else:
            final_img = img_data.getvalue()
            msg = MessageChain.create(Image(data_bytes=final_img))

        await safeSendGroupMessage(
            group,
            MessageChain.create(
                At(member.id),
                Plain(
                    f" 成功将图片放大 {img_scale} 倍，尺寸为：{img.size[0]}x{img.size[1]}，总耗时 {time_recorder.total()}\n"
                ),
            )
            + msg,
        )

    else:
        await safeSendGroupMessage(
            group, MessageChain.create(At(member.id), Plain(f"你的{COIN_NAME}不足"))
        )

    MEMBER_RUNING_LIST.remove(member.id)


@channel.use(ListenerSchema(listening_events=[ApplicationShutdowned]))
async def stopEvents():
    await asyncio.sleep(2)
    waifu2x.stop()
