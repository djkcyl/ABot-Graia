import hashlib
import zipfile
import asyncio
import numpy as np

from io import BytesIO
from pathlib import Path
from loguru import logger
from PIL import Image as IMG
from realesrgan import RealESRGANer
from graia.saya import Saya, Channel
from graia.ariadne.model import Group, Member
from basicsr.archs.rrdbnet_arch import RRDBNet
from graia.broadcast.interrupt.waiter import Waiter
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import GroupMessage
from graia.broadcast.interrupt import InterruptControl
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.element import At, Image, Plain, Source
from graia.ariadne.message.parser.twilight import Twilight, ElementMatch, FullMatch

from database.db import reduce_gold
from util.update_cos import UpdateCos
from util.TimeTool import TimeRecorder
from util.control import Permission, Interval
from util.QRGeneration import QRcode_generation
from util.sendMessage import safeSendGroupMessage
from config import yaml_data, group_data, COIN_NAME


MEMBER_RUNING_LIST = []
BASE_DIR = Path(__file__).parent
saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
inc = InterruptControl(bcc)
upsampler = RealESRGANer(
    scale=4,
    model_path=str(BASE_DIR.joinpath("RealESRGAN_x4plus_anime_6B.pth")),
    model=RRDBNet(
        num_in_ch=3,
        num_out_ch=3,
        num_feat=64,
        num_block=6,
        num_grow_ch=32,
        scale=4,
    ),
    tile=0,
    tile_pad=10,
    pre_pad=0,
    half=False,
)


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
        yaml_data["Saya"]["Real-ESRGAN"]["Disabled"]
        and group.id != yaml_data["Basic"]["Permission"]["DebugGroup"]
    ):
        return
    elif "Real-ESRGAN" in group_data[str(group.id)]["DisabledFunc"]:
        return

    @Waiter.create_using_function(
        listening_events=[GroupMessage], using_decorators=[Permission.require()]
    )
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

    image: np.ndarray = IMG.open(BytesIO(image_data)).__array__()
    img_x, img_y = image.shape[0], image.shape[1]
    size = img_x * img_y
    size_max = max(image.shape)

    if size_max > 1000:
        outscale = 1.5
    else:
        outscale = 2

    max_size = yaml_data["Saya"]["Real-ESRGAN"]["MaxSize"]

    if size > max_size:
        MEMBER_RUNING_LIST.remove(member.id)
        return await safeSendGroupMessage(
            group, MessageChain.create(f"图片尺寸过大，暂不提供服务，请发送总像素小于 {max_size} 的图片")
        )

    if await reduce_gold(str(member.id), 10):
        await safeSendGroupMessage(group, MessageChain.create("正在处理，请稍候"), quote=source)
        time_recorder = TimeRecorder()
        output, _ = await asyncio.to_thread(upsampler.enhance, image, outscale=outscale)
        img = IMG.fromarray(output)

        if yaml_data["Saya"]["Real-ESRGAN"]["UpdateCos"]:
            img_data = BytesIO()
            img.save(img_data, format="PNG")
            logger.info(f"图片超分处理成功 {img.size[0]}x{img.size[1]}")
            image_md5 = hashlib.md5(img_data.getvalue()).hexdigest()
            zip_bio = BytesIO()
            with zipfile.ZipFile(
                zip_bio,
                "w",
                allowZip64=False,
                compression=zipfile.ZIP_BZIP2,
            ) as zipFile:
                zipFile.writestr(
                    f"{image_md5}.png",
                    img_data.getvalue(),
                )
            cos = UpdateCos(zip_bio.getvalue(), f"Real-ESRGAN/{image_md5}.zip")
            await cos.update()
            url = await cos.get_url()
            final_img = QRcode_generation(url)
            msg = MessageChain.create(
                Plain("请扫码二维码下载\n"),
                Image(data_bytes=final_img),
                Plain("\n本链接仅在 10 分钟内可用，请尽快保存。"),
            )
        else:
            img_data = BytesIO()
            img.save(img_data, format="JPEG")
            logger.info(f"图片超分处理成功 {img.size[0]}x{img.size[1]}")
            final_img = img_data.getvalue()
            msg = MessageChain.create(Image(data_bytes=final_img))

        await safeSendGroupMessage(
            group,
            MessageChain.create(
                At(member.id),
                Plain(f" 图片超分成功，总耗时 {time_recorder.total()}\n"),
            )
            + msg,
        )
    else:
        await safeSendGroupMessage(
            group, MessageChain.create(At(member.id), Plain(f"你的{COIN_NAME}不足"))
        )

    MEMBER_RUNING_LIST.remove(member.id)
