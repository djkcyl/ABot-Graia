# import os
# import time
# import requests

# from hashlib import md5
# from graiax import silkcoder
# from graia.saya import Saya, Channel
# from graia.application import GraiaMiraiApplication
# from graia.saya.builtins.broadcast.schema import ListenerSchema
# from graia.application.event.messages import Group, GroupMessage
# from graia.application.message.parser.literature import Literature
# from graia.application.message.elements.internal import Source, Plain, MessageChain, Voice_LocalFile
# # from google_trans_new import google_translator

# from config import yaml_data, group_data, sendmsg

# from .post_tts_text import post_text


# saya = Saya.current()
# channel = Channel.current()

# if not os.path.exists("voice_file"):
#     print("正在创建语音缓存文件夹")
#     os.mkdir("voice_file")

# TTSRUNING = False

# # trans = google_translator()


# @channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("/tts")]))
# async def ali_tts(app: GraiaMiraiApplication, group: Group, message: MessageChain, source: Source):

#     if yaml_data['Saya']['AliTTS']['Disabled']:
#         return await sendmsg(app=app, group=group)
#     elif 'AliTTS' in group_data[group.id]['DisabledFunc']:
#         return await sendmsg(app=app, group=group)

#     if len(message.asDisplay()) > 180:
#         await app.sendGroupMessage(group, MessageChain.create([
#             Plain(f"超过字符限制 " + str(len(message.asDisplay())) + "/180")
#         ]))
#         return
#     saying = message.asDisplay().split(" ", 2)
#     tts_con = saying[1]
#     model = ["男", "女", "童", "日", "美"]
#     strmodel = "、".join(model)
#     ttstext = saying[2]
#     if tts_con not in model:
#         await app.sendGroupMessage(group, MessageChain.create([Plain(f"请输入可用的语音模型\n{strmodel}")]))
#         return
#     if tts_con == "男":
#         vm_type = "zhichu"
#     elif tts_con == "女":
#         vm_type = "zhiqi"
#     elif tts_con == "童":
#         vm_type = "aibao"
#     elif tts_con == "日":
#         # ttstext = trans.translate(ttstext, lang_tgt='ja')
#         # await app.sendGroupMessage(group, MessageChain.create([Plain(f"已将文本使用谷歌翻译转换为日语：\n{ttstext}")]))
#         vm_type = "tomoka"
#     elif tts_con == "美":
#         # ttstext = trans.translate(ttstext, lang_tgt='en')
#         # await app.sendGroupMessage(group, MessageChain.create([Plain(f"已将文本使用谷歌翻译转换为英语：\n{ttstext}")]))
#         vm_type = "abby"
#     # elif tts_con == "A":
#     #     vm_type = "pt_zbwn4r07awdszw0b_a60voice"
#     # print(tts_con)
#     tts_md5 = md5(str(saying[1] + ttstext).encode(encoding="UTF-8")).hexdigest()
#     tts_shot_md5 = tts_md5[0:2]
#     # print(tts_shot_md5)
#     voice_file = "voice_file/" + tts_shot_md5 + "/" + tts_md5  # 完整 md5 文件名
#     voice_file_path = "voice_file/" + tts_shot_md5  # md5 文件夹名
#     if not os.path.exists(voice_file_path):  # 判断语音 md5 文件夹是否存在
#         # print("md5短文件夹不存在，正在创建")
#         os.mkdir(voice_file_path)
#     if os.path.exists(voice_file + ".silk"):  # 判断语音文件是否存在
#         # print("语音文件存在，正在发送")
#         await app.sendGroupMessage(group, MessageChain.create([  # 发送语音silk文件
#             Plain(f"{tts_md5}.silk\n语音文件存在，正在发送")
#         ]))
#         await app.sendGroupMessage(group, MessageChain.create([  # 发送语音silk文件
#             Voice_LocalFile(voice_file + ".silk")
#         ]))
#     else:
#         # print("语音文件不存在，正在创建，请耐心等待")
#         global TTSRUNING
#         if TTSRUNING:
#             await app.sendGroupMessage(group, MessageChain.create([
#                 Plain(f"当前有一个tts请求正在运行中，请稍后……")
#             ]))
#             return
#         TTSRUNING = True
#         loop_wait = await app.sendGroupMessage(group, MessageChain.create([
#             Plain(f"正在创建语音文件，请耐心等待")
#         ]))
#         time1 = time.time()
#         tts_file_url = await post_text(ttstext, vm_type)
#         r = requests.get(tts_file_url)
#         with open(voice_file + '.wav', 'wb') as f:
#             f.write(r.content)
#         await silkcoder.encode(voice_file + '.wav', voice_file + '.silk')
#         os.remove(voice_file + ".wav")
#         time2 = time.time()
#         times = str(int(time2 - time1))
#         await app.sendGroupMessage(group, MessageChain.create([
#             Voice_LocalFile(voice_file + ".silk")
#         ]))
#         await app.sendGroupMessage(group, MessageChain.create([
#             Plain(f"语音创建完成！耗时 {times} 秒\n{tts_md5}.silk")
#         ]), quote=source)
#         await app.revokeMessage(loop_wait)
#         TTSRUNING = False