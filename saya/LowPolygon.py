import httpx
import asyncio
import triangler
import matplotlib.pyplot as plt

from io import BytesIO
from PIL import Image as IMG
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group, Member
from graia.broadcast.interrupt.waiter import Waiter
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.broadcast.interrupt import InterruptControl
from graia.ariadne.message.parser.literature import Literature
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.element import Plain, At, Source, Image

from config import yaml_data, group_data
from util.sendMessage import safeSendGroupMessage
from util.control import Permission, Interval, Rest


saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
inc = InterruptControl(bcc)

WAITING = []


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Literature("低多边形")],
        decorators=[Rest.rest_control(), Permission.require(), Interval.require()],
    )
)
async def low_poly(
    app: Ariadne, group: Group, message: MessageChain, member: Member, source: Source
):

    if yaml_data["Saya"]["LowPolygon"]["Disabled"]:
        return
    elif "LowPolygon" in group_data[str(group.id)]["DisabledFunc"]:
        return

    @Waiter.create_using_function([GroupMessage])
    async def waiter1(
        waiter1_group: Group, waiter1_member: Member, waiter1_message: MessageChain
    ):
        if waiter1_group.id == group.id and waiter1_member.id == member.id:
            waiter1_saying = waiter1_message.asDisplay()
            if waiter1_saying == "取消":
                return False
            elif waiter1_message.has(Image):
                return waiter1_message.getFirst(Image).url
            else:
                await safeSendGroupMessage(group, MessageChain.create([Plain("请发送图片")]))

    if member.id not in WAITING:
        WAITING.append(member.id)

        if message.has(Image):
            image_url = message.getFirst(Image).url
        elif message.has(At):
            atid = message.getFirst(At).target
            image_url = f"http://q1.qlogo.cn/g?b=qq&nk={atid}&s=640"
        else:
            await safeSendGroupMessage(
                group, MessageChain.create([At(member.id), Plain(" 请发送图片以进行制作")])
            )
            try:
                image_url = await asyncio.wait_for(inc.wait(waiter1), timeout=30)
                if not image_url:
                    WAITING.remove(member.id)
                    return await safeSendGroupMessage(
                        group, MessageChain.create([Plain("已取消")])
                    )
            except asyncio.TimeoutError:
                WAITING.remove(member.id)
                return await safeSendGroupMessage(
                    group, MessageChain.create([Plain("等待超时")]), quote=source.id
                )

        async with httpx.AsyncClient() as client:
            resp = await client.get(image_url)
            img_bytes = resp.content
        await safeSendGroupMessage(group, MessageChain.create([Plain("正在生成，请稍后")]))
        image = await asyncio.to_thread(make_low_poly, img_bytes)
        await safeSendGroupMessage(
            group, MessageChain.create([Image(data_bytes=image)])
        )
        WAITING.remove(member.id)


def make_low_poly(img_bytes):

    img = IMG.open(BytesIO(img_bytes)).convert("RGB")
    img.thumbnail((600, 600))
    imgx, imgy = img.size
    t = triangler.Triangler(
        sample_method=triangler.SampleMethod.POISSON_DISK, points=max(imgx, imgy)
    )
    img = plt.imsave(bio := BytesIO(), t.convert(img.__array__()))
    img = IMG.open(bio).convert("RGB")
    img.save(bio := BytesIO(), "JPEG")

    return bio.getvalue()
