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
