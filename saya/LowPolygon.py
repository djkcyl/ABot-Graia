import httpx
import asyncio
import triangler
import matplotlib.pyplot as plt

from io import BytesIO
from typing import Optional
from PIL import Image as IMG
from graia.saya import Saya, Channel
from graia.ariadne.model import Group, Member
from graia.broadcast.interrupt.waiter import Waiter
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.broadcast.interrupt import InterruptControl
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.element import Plain, At, Source, Image
from graia.ariadne.message.parser.twilight import Twilight, Sparkle
from graia.ariadne.message.parser.pattern import FullMatch, ArgumentMatch, RegexMatch

from config import yaml_data, group_data
from util.sendMessage import safeSendGroupMessage
from util.control import Permission, Interval, Rest


saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
inc = InterruptControl(bcc)

WAITING = []


class LowPolySparkle(Sparkle):
    header = FullMatch("低多边形")
    args = ArgumentMatch("-P", action="store", regex="\\d+", optional=True)
    anythings1 = RegexMatch(".*")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[Twilight(LowPolySparkle)],
        decorators=[Rest.rest_control(), Permission.require(), Interval.require()],
    )
)
async def low_poly(
    group: Group,
    member: Member,
    source: Source,
    sparkle: Sparkle,
):

    if (
        yaml_data["Saya"]["LowPolygon"]["Disabled"]
        and group.id != yaml_data["Basic"]["Permission"]["DebugGroup"]
    ):
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

        saying: LowPolySparkle = sparkle
        image_url = None
        point = None

        if saying.args.matched:
            point = int(saying.args.result)
            if 99 < point < 3001:
                point = point
            else:
                return await safeSendGroupMessage(
                    group, MessageChain.create([Plain("-P ：请输入100-3000之间的整数")])
                )

        if saying.anythings1.matched:
            if saying.anythings1.result.has(Image):
                image_url = saying.anythings1.result.getFirst(Image).url
            elif saying.anythings1.result.has(At):
                atid = saying.anythings1.result.getFirst(At).target
                image_url = f"http://q1.qlogo.cn/g?b=qq&nk={atid}&s=640"

        if not image_url:
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
        await safeSendGroupMessage(
            group, MessageChain.create([Plain(f"正在生成{point if point else '默认'}切面，请稍后")])
        )
        image = await asyncio.to_thread(make_low_poly, img_bytes, point)
        await safeSendGroupMessage(
            group, MessageChain.create([Image(data_bytes=image)])
        )
        WAITING.remove(member.id)


def make_low_poly(img_bytes, point: Optional[int] = None):

    img = IMG.open(BytesIO(img_bytes)).convert("RGB")
    img.thumbnail((1000, 1000))
    imgx, imgy = img.size
    t = triangler.Triangler(
        sample_method=triangler.SampleMethod.POISSON_DISK,
        points=point if point else max(imgx, imgy),
    )
    img = plt.imsave(bio := BytesIO(), t.convert(img.__array__()))
    img = IMG.open(bio).convert("RGB")
    img.save(bio := BytesIO(), "JPEG")

    return bio.getvalue()
