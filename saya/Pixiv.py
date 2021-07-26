# import json
# import random
# import requests
# import aiohttp

# from PIL import Image as PI
# from io import BytesIO
# from graia.application import GraiaMiraiApplication
# from graia.saya import Saya, Channel
# from graia.saya.builtins.broadcast.schema import ListenerSchema
# from graia.application.event.messages import *
# from graia.application.event.mirai import *
# from graia.application.message.elements.internal import *

# from config import yaml_data, group_data

# saya = Saya.current()
# channel = Channel.current()


# @channel.use(ListenerSchema(listening_events=[GroupMessage]))
# async def main(app: GraiaMiraiApplication, group: Group, message: MessageChain):

#     saying = message.asDisplay().split(" ", 1)
#     if saying[0] in ['色图', '涩图', '瑟图', 'setu']:

#         if yaml_data['Saya']['Pixiv']['Disabled']:
#             return
#         elif 'Pixiv' in group_data[group.id]['DisabledFunc']:
#             return

#         await app.sendGroupMessage(group, MessageChain.create([Image_UnsafeBytes()]))
#         if len(saying) == 1:
#             try:
#                 picid = asynchttp.get(url='http://a60.one:404').json()['pic']
#                 imgbio = BytesIO()
#                 imgcon = await asynchttp.get(url=f"http://pic.a60.one:88/{picid}.jpg").content
#                 imgbio.write(imgcon)
#                 img = PI.open(imgbio.getvalue())
#                 img_x, img_y = img.size
#                 imgsize = img.size
#                 img_ratio = img_x / img_y
#                 img_resolution = (20, int(20 / img_ratio))
#                 img = img.resize(img_resolution)
#                 img = img.resize(imgsize, resample=Image.BOX)
#                 img.save(imgbio, format="JPEG", quality=40)
#                 await app.sendGroupMessage(group, MessageChain.create([
#                     Image_UnsafeBytes(imgbio.getvalue()),
#                     Plain(f"ID：{picid}")
#                 ]))
#             except:
#                 await app.sendGroupMessage(group, MessageChain.create([
#                     Plain(f"慢一点慢一点，再冲就冲死啦")
#                 ]))
#         # if len(saying) == 2:
#         #     try:
#         #         picid = random.choice(json.loads(
#         #             requests.get(
#         #                 f'http://a60.one:404/get/tags/{saying[1]}').text)['data']['pic_list'])['pic']
#         #         await app.sendGroupMessage(group, MessageChain.create([Image_NetworkAddress(f"http://pic.a60.one:88/{picid}.jpg")]))
#         #     except:
#         #         await app.sendGroupMessage(group, MessageChain.create([Plain(f"慢一点慢一点，再冲就冲死啦")]))
#         #         await app.sendGroupMessage(group, MessageChain.create([Plain(f"ID：{picid}")]))
