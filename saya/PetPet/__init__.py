import os
import numpy
import aiohttp

from io import BytesIO
from PIL import ImageOps
from PIL import Image as IMG
from graia.saya import Saya, Channel
from graia.application.event.messages import Group
from graia.application import GraiaMiraiApplication
from graia.application.event.mirai import NudgeEvent
from graia.application.exceptions import AccountMuted
from graia.application.message.chain import MessageChain
from moviepy.editor import ImageSequenceClip as imageclip
from graia.application.event.messages import GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.elements.internal import At, Image, Plain

from util.limit import manual_limit
from config import yaml_data, group_data
from util.RestControl import rest_control
from util.UserBlock import black_list_block


saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            headless_decorators=[rest_control(), black_list_block()]))
async def petpet_generator(app: GraiaMiraiApplication, message: MessageChain, group: Group):

    if yaml_data['Saya']['PetPet']['Disabled'] and not yaml_data['Saya']['PetPet']['CanAt']:
        return
    elif 'PetPet' in group_data[group.id]['DisabledFunc']:
        return
    message_text = message.asDisplay()
    if message.has(At) and message_text.startswith("摸") or message_text.startswith("摸头 "):
        manual_limit(group.id, "petpet", 3)
        if not os.path.exists("./saya/PetPet/temp"):
            os.mkdir("./saya/PetPet/temp")
        await petpet(message.get(At)[0].target)
        await app.sendGroupMessage(group, MessageChain.create([
            Image.fromLocalFile(f"./saya/PetPet/temp/tempPetPet-{message.get(At)[0].target}.gif")
        ]))


@channel.use(ListenerSchema(listening_events=[NudgeEvent],
                            headless_decorators=[rest_control(), black_list_block()]))
async def get_nudge(app: GraiaMiraiApplication, nudge: NudgeEvent):

    if yaml_data['Saya']['PetPet']['Disabled'] and not yaml_data['Saya']['PetPet']['CanNudge']:
        return
    elif 'PetPet' in group_data[nudge.group_id]['DisabledFunc']:
        return

    manual_limit(nudge.group_id, "petpet", 3)

    app.logger.info(f"[{nudge.group_id}] 收到戳一戳事件 -> [{nudge.target}]")
    if not os.path.exists("./saya/PetPet/temp"):
        os.mkdir("./saya/PetPet/temp")

    await app.sendGroupMessage(nudge.group_id, MessageChain.create([
        Plain("收到 "),
        At(nudge.supplicant),
        Plain(" 的戳一戳，正在制图")
    ]))

    await petpet(nudge.target)
    await app.sendGroupMessage(nudge.group_id, MessageChain.create([
        Image.fromLocalFile(
            f"./saya/PetPet/temp/tempPetPet-{nudge.target}.gif")
    ]))


frame_spec = [
    (27, 31, 86, 90),
    (22, 36, 91, 90),
    (18, 41, 95, 90),
    (22, 41, 91, 91),
    (27, 28, 86, 91)
]

squish_factor = [
    (0, 0, 0, 0),
    (-7, 22, 8, 0),
    (-8, 30, 9, 6),
    (-3, 21, 5, 9),
    (0, 0, 0, 0)
]

squish_translation_factor = [0, 20, 34, 21, 0]

frames = tuple([f'./saya/PetPet/PetPetFrames/frame{i}.png' for i in range(5)])


async def save_gif(gif_frames, dest, fps=10):

    clip = imageclip(gif_frames, fps=fps)
    clip.write_gif(dest)  # 使用 imageio
    clip.close()


# 生成函数（非数学意味）
async def make_frame(avatar, i, squish=0, flip=False):
    # 读入位置
    spec = list(frame_spec[i])
    # 将位置添加偏移量
    for j, s in enumerate(spec):
        spec[j] = int(s + squish_factor[i][j] * squish)
    # 读取手
    hand = IMG.open(frames[i])
    # 反转
    if flip:
        avatar = ImageOps.mirror(avatar)
    # 将头像放缩成所需大小
    avatar = avatar.resize(
        (int((spec[2] - spec[0]) * 1.2), int((spec[3] - spec[1]) * 1.2)), IMG.ANTIALIAS)
    # 并贴到空图像上
    gif_frame = IMG.new('RGB', (112, 112), (255, 255, 255))
    gif_frame.paste(avatar, (spec[0], spec[1]))
    # 将手覆盖（包括偏移量）
    gif_frame.paste(
        hand, (0, int(squish * squish_translation_factor[i])), hand)
    # 返回
    return numpy.array(gif_frame)


async def petpet(member_id, flip=False, squish=0, fps=20) -> None:

    url = f'http://q1.qlogo.cn/g?b=qq&nk={str(member_id)}&s=640'
    gif_frames = []
    # 打开头像
    # avatar = Image.open(path)
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url) as resp:
            img_content = await resp.read()

    avatar = IMG.open(BytesIO(img_content))

    # 生成每一帧
    for i in range(5):
        gif_frames.append(await make_frame(avatar, i, squish=squish, flip=flip))
    # 输出
    await save_gif(gif_frames, f'./saya/PetPet/temp/tempPetPet-{member_id}.gif', fps=fps)
