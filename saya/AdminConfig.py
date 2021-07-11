from graia.application import GraiaMiraiApplication
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.event.messages import *
from graia.application.event.mirai import *
from graia.application.message.elements.internal import *
from graia.application.message.parser.literature import Literature
import yaml

from config import yaml_data

saya = Saya.current()
channel = Channel.current()


funclist = [
    {"name": "阿里云tts", "key": "AliTTS"},
    {"name": "小鸡词典查梗", "key": "ChickDict"},
    {"name": "小鸡词典emoji转换", "key": "ChickEmoji"},
    {"name": "汉语词典查询", "key": "ChineseDict"},
    {"name": "网易云音乐点歌", "key": "CloudMusic"},
    {"name": "网络黑话翻译", "key": "CyberBlacktalk"},
    {"name": "词云", "key": "WordCloud"},
    {"name": "禁言套餐", "key": "MutePack"},
    {"name": "兽语转换", "key": "Beast"},
    {"name": "我的世界服务器Ping", "key": "MinecraftPing"},
    {"name": "摸头", "key": "PetPet"},
    {"name": "Pornhub风格logo生成", "key": "PornhubLogo"},
    {"name": "复读姬", "key": "Repeater"},
    {"name": "涩图", "key": "Pixiv"},
]


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def adminmain(app: GraiaMiraiApplication, group: Group, message: MessageChain):
    if message.asDisplay() in ["/help", "帮助", "菜单"]:
        await app.sendGroupMessage(group, MessageChain.create([Plain(f"{yaml_data['Basic']['BotName']} 使用指南"),
                                                               Plain(f"\n（使用指南还没写，别急。急着需要可以去GitHub"),
                                                               Plain(f"\nhttps://github.com/djkcyl/ABot-Graia"),
                                                               Plain(f"\n发送 <管理员菜单> 即可调整群内功能是否开启")]))


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("管理员菜单")]))
async def adminmain(app: GraiaMiraiApplication, group: Group, member: Member):
    if member.permission in ["Administrator", "Owner"] or member.id in yaml_data['Basic']['Permission']['Admin']:
        msg = []
        msg.append(Plain(f"机器人群管理菜单\n===================\n当前有以下功能可以调整："))
        i = 1
        for func in funclist:
            funcname = func["name"]
            funckey = func["key"]
            funcglobal = yaml_data["Saya"][funckey]["Disabled"]
            funcblacklist = yaml_data["Saya"][funckey]["Blacklist"]
            if funcglobal:
                statu = "全局关闭"
            elif group.id in funcblacklist:
                statu = "本群关闭"
            else:
                statu = "本群开启"
            msg.append(
                Plain(f"\n{str(i)}.{funcname}：{statu}"))
            i += 1
        msg.append(Plain(
            f"\n===================\n开启/关闭 <功能id>\n如有功能在开启后仍为禁用状态，则为全局禁用\n更多功能待开发，如有特殊需求可以@{yaml_data['Basic']['BotName']}后向{yaml_data['Basic']['Permission']['MasterName']}询问"))
        await app.sendGroupMessage(group, MessageChain.create(msg))
    else:
        await app.sendGroupMessage(group, MessageChain.create([Plain(f"你没有使用该功能的权限")]))


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("开启")]))
async def onAoff(app: GraiaMiraiApplication, group: Group, member: Member, message: MessageChain):
    if member.permission in ["Administrator", "Owner"] or member.id in yaml_data['Basic']['Permission']['Admin']:
        saying = message.asDisplay().split()
        sayfunc = int(saying[1]) - 1
        func = funclist[sayfunc]
        funcname = func["name"]
        funckey = func["key"]
        funcdisabled = yaml_data["Saya"][funckey]["Disabled"]
        funcblacklist = yaml_data["Saya"][funckey]["Blacklist"]
        if funcdisabled:
            await app.sendGroupMessage(group, MessageChain.create([Plain(f"{funcname}当前处于全局禁用状态")]))
        elif group.id in funcblacklist:
            funcblacklist.remove(group.id)
            yaml_data["Saya"][funckey]["Blacklist"] = funcblacklist
            with open("config.yaml", 'w', encoding="utf-8") as f:
                yaml.dump(yaml_data, f, allow_unicode=True)
            await app.sendGroupMessage(group, MessageChain.create([Plain(f"{funcname}已开启")]))
        else:
            await app.sendGroupMessage(group, MessageChain.create([Plain(f"{funcname}已处于开启状态")]))
    else:
        await app.sendGroupMessage(group, MessageChain.create([Plain(f"你没有使用该功能的权限")]))


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("关闭")]))
async def onAoff(app: GraiaMiraiApplication, group: Group, member: Member, message: MessageChain):
    if member.permission in ["Administrator", "Owner"] or member.id in yaml_data['Basic']['Permission']['Admin']:
        saying = message.asDisplay().split()
        sayfunc = int(saying[1]) - 1
        func = funclist[sayfunc]
        funcname = func["name"]
        funckey = func["key"]
        funcblacklist = yaml_data["Saya"][funckey]["Blacklist"]
        if group.id not in funcblacklist:
            print(funcblacklist)
            funcblacklist.append(group.id)
            yaml_data["Saya"][funckey]["Blacklist"] = funcblacklist
            with open("config.yaml", 'w', encoding="utf-8") as f:
                yaml.dump(yaml_data, f, allow_unicode=True)
            print(yaml_data["Saya"][funckey]["Blacklist"])
            await app.sendGroupMessage(group, MessageChain.create([Plain(f"{funcname}已关闭")]))
        else:
            await app.sendGroupMessage(group, MessageChain.create([Plain(f"{funcname}已处于关闭状态")]))
    else:
        await app.sendGroupMessage(group, MessageChain.create([Plain(f"你没有使用该功能的权限")]))


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def tran(app: GraiaMiraiApplication, group: Group, member: Member, message: MessageChain):
    if message.has(At) and message.getOne(At, 0).target == yaml_data['Basic']['MAH']['BotQQ']:
        saying = message.asDisplay()
        await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
            Plain(f"收到传送消息："),
            Plain(f"\n群号：{group.id}"),
            Plain(f"\n群名：{group.name}"),
            Plain(f"\nQQ：{member.id}"),
            Plain(f"\n昵称：{member.name}"),
            Plain(f"\n=================="),
            Plain(f"\n消息内容：{saying}")]))
