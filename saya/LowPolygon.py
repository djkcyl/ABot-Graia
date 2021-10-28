import httpx
import asyncio
import triangler
import matplotlib.pyplot as plt

from io import BytesIO
from PIL import Image as IMG
from graia.saya import Saya, Channel
from graia.application.group import Group, Member
from concurrent.futures import ThreadPoolExecutor
from graia.application import GraiaMiraiApplication
from graia.broadcast.interrupt.waiter import Waiter
from graia.broadcast.interrupt import InterruptControl
from graia.application.event.messages import GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.parser.literature import Literature
from graia.application.message.elements.internal import MessageChain, Plain, At, Image_UnsafeBytes, Source, Image

from config import yaml_data, group_data
from util.limit import member_limit_check
from util.RestControl import rest_control
from util.UserBlock import group_black_list_block


saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
inc = InterruptControl(bcc)
loop = asyncio.get_event_loop()
pool = ThreadPoolExecutor(4)

WAITING = []


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Literature("低多边形")],
                            headless_decorators=[rest_control(), member_limit_check(60), group_black_list_block()]))
async def low_poly(app: GraiaMiraiApplication, group: Group, message: MessageChain, member: Member, source: Source):

    if yaml_data['Saya']['LowPolygon']['Disabled']:
        return
    elif 'LowPolygon' in group_data[group.id]['DisabledFunc']:
        return

    @Waiter.create_using_function([GroupMessage])
    async def waiter1(waiter1_group: Group, waiter1_member: Member, waiter1_message: MessageChain):
        if waiter1_group.id == group.id and waiter1_member.id == member.id:
            waiter1_saying = waiter1_message.asDisplay()
            if waiter1_saying == "取消":
                return False
            elif waiter1_message.has(Image):
                return waiter1_message.getFirst(Image).url
            else:
                await app.sendGroupMessage(group, MessageChain.create([Plain("请发送图片")]))

    if member.id not in WAITING:
        WAITING.append(member.id)

        if message.has(Image):
            image_url = message.getFirst(Image).url
        elif message.has(At):
            atid = message.getFirst(At).target
            image_url = f"http://q1.qlogo.cn/g?b=qq&nk={atid}&s=640"
        else:
            await app.sendGroupMessage(group, MessageChain.create([
                At(member.id),
                Plain(" 请发送图片以进行制作")
            ]))
            try:
                image_url = await asyncio.wait_for(inc.wait(waiter1), timeout=30)
                if not image_url:
                    WAITING.remove(member.id)
                    return await app.sendGroupMessage(group, MessageChain.create([Plain("已取消")]))
            except asyncio.TimeoutError:
                WAITING.remove(member.id)
                return await app.sendGroupMessage(group, MessageChain.create([
                    Plain("等待超时")
                ]), quote=source)

        async with httpx.AsyncClient() as client:
            resp = await client.get(image_url)
            img_bytes = resp.content
        await app.sendGroupMessage(group, MessageChain.create([Plain("正在生成，请稍后")]))
        image = await loop.run_in_executor(pool, make_low_poly, img_bytes)
        await app.sendGroupMessage(group, MessageChain.create([
            Image_UnsafeBytes(image)
        ]))
        WAITING.remove(member.id)


def make_low_poly(img_bytes):

    img = IMG.open(BytesIO(img_bytes)).convert("RGB")
    imgx, imgy = img.size
    t = triangler.Triangler(sample_method=triangler.SampleMethod.POISSON_DISK, points=max(imgx, imgy))
    img = plt.imsave(bio := BytesIO(), t.convert(img.__array__()))
    img = IMG.open(bio).convert("RGB")
    img.save(bio := BytesIO(), "JPEG")

    return bio.getvalue()
