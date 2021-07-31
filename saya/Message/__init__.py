from graia.saya import Saya, Channel
from graia.application.group import Group
from graia.application import GraiaMiraiApplication
from graia.broadcast.interrupt import InterruptControl
from graia.application.event.messages import GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.parser.literature import Literature
from graia.application.message.elements.internal import MessageChain, Plain, At, Image_LocalFile

from config import yaml_data, group_data


saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
inc = InterruptControl(bcc)


# baidu_Token_api = f'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={configs["API Key"]}&client_secret={configs["Secret Key"]}'
# r = requests.get(baidu_Token_api)
# _Token = json.loads(r.text)['access_token']
# print(_Token)


# @channel.use(ListenerSchema(listening_events=[GroupMessage]))
# async def message_review(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
#     global _Token
#     if group.id == 790380594:
#         message_id = message.getFirst(Source).id

#         # 判断是否包含图片
#         # if message.has(Image):
#         #     message_image = message.get(Image)

#         if message.has(Plain):
#             print("检测到文本")
#             message_text = message.asDisplay().replace(
#                 "[图片]", "").replace("[表情]", "").replace("\n", "").strip("")
#             censor = text_censor(message_text, _Token)
#             if censor["conclusionType"] != 1:
#                 await app.sendGroupMessage(group.id, MessageChain.create([Plain(censor["data"][0]["msg"])]))
#                 await app.revokeMessage(message_id)
#                 await app.mute(group, member.id, 5)
#                 # await app.unmute(group, member.id)

#         message_plain = message.asMerged()

#         # print(message.asDisplay())
#         # print(message.get(Image))
#         print(message_text)
#         # await app.sendGroupMessage(group.id, MessageChain.create([Plain("爬")]), quote=message_id)
#         # await app.revokeMessage(message_id)
#         # await app.mute(group, member.id, 2592000)
#         # await app.unmute(group, member.id)
#         # print(message_id)


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("/ping943")]))
async def ping943(app: GraiaMiraiApplication, group: Group, message: MessageChain):
    saylist = message.asDisplay().split()
    saylistnum = len(saylist)
    if saylistnum == 3:
        if saylist[1] == "t":
            i = 0
            atnum = []
            while i < int(saylist[2]):
                atnum.append(At(target=568248266))
                atnum.append(Plain(" "))
                i += 1
            print(atnum)
            await app.sendGroupMessage(group, MessageChain.create([Plain(f"正在ping {i} 次")]))
            await app.sendGroupMessage(group, MessageChain.create(atnum))
        else:
            await app.sendGroupMessage(group, MessageChain.create([Plain("使用方法：/ping943 [t *int]")]))
    elif saylistnum == 2:
        if saylist[1] == "t":
            await app.sendGroupMessage(group, MessageChain.create([Plain("请输入ping次数")]))
        else:
            await app.sendGroupMessage(group, MessageChain.create([Plain("使用方法：/ping943 [t *int]")]))
    elif saylist[0] == "/ping943":
        await app.sendGroupMessage(group, MessageChain.create([At(568248266)]))


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def a_plant(app: GraiaMiraiApplication, group: Group, message: MessageChain):
    
    if yaml_data['Saya']['Message']['Disabled']:
        return
    elif 'Message' in group_data[group.id]['DisabledFunc']:
        return
    
    saying = message.asDisplay()
    if saying == "草":
        await app.sendGroupMessage(group, MessageChain.create([
            Plain(f"一种植物（")
        ]))
    if saying == "好耶":
        await app.sendGroupMessage(group, MessageChain.create([
            Image_LocalFile("./saya/Message/haoye.png")
        ]))
    if saying == "流汗黄豆.jpg":
        await app.sendGroupMessage(group, MessageChain.create([
            Image_LocalFile("./saya/Message/huangdou.jpg")
        ]))


# @channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("/bantime")]))
# async def kickall(app: GraiaMiraiApplication, group: Group):
#     n1 = '2021-06-16 18:00:19'
#     struct_time1, struct_time2 = time.time(), time.strptime(n1, '%Y-%m-%d %H:%M:%S')
#     struct_time2 = time.mktime(struct_time2)
#     diff_time = struct_time2 - struct_time1
#     struct_time = time.gmtime(diff_time)

#     await app.sendGroupMessage(group, MessageChain.create([
#         Plain('距离解封还有{2}日{3}小时{4}分钟{5}秒'.format(
#             struct_time.tm_year-1970,
#             struct_time.tm_mon-1,
#             struct_time.tm_mday-1,
#             struct_time.tm_hour,
#             struct_time.tm_min,
#             struct_time.tm_sec
#         ))]))


# @channel.use(SchedulerSchema(crontabify("* * * * * *")))
# async def something_scheduled(app: GraiaMiraiApplication):
#     await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([Plain("定时消息发送测试")]))
