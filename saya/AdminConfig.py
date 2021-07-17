from graia.application import GraiaMiraiApplication
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.event.messages import *
from graia.application.event.mirai import *
from graia.application.message.elements.internal import *
from graia.application.message.parser.literature import Literature

from config import save_config, yaml_data, group_data

saya = Saya.current()
channel = Channel.current()


funcList = [
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
    {"name": "风格logo生成", "key": "StyleLogoGenerator"},
    {"name": "复读姬", "key": "Repeater"},
    {"name": "涩图", "key": "Pixiv"},
    {"name": "人工智障聊天", "key": "ChatMS"},
    {"name": "没啥用的回复", "key": "Message"},
]

configList = [
    {"name": "入群欢迎", "key": "WelcomeMSG"},
    {"name": "退群通知", "key": "LeaveMSG"}
]
groupInitData = {
    "DisabledFunc": ["A"],
    "WelcomeMSG": {
        "Enabled": False,
        "Message": None
    }
}


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("初始化")]))
async def groupDataInit(app: GraiaMiraiApplication, member: Member):
    if member.id == yaml_data['Basic']['Permission']['Master']:
        print("正在进行群配置初始化")
        groupList = await app.groupList()
        groupNum = len(groupList)
        print(f"当前 {yaml_data['Basic']['BotName']} 共加入了 {groupNum} 个群")
        for group in groupList:
            if group.id not in group_data:
                group_data[group.id] = groupInitData
                print(group_data[group.id])
                print(f"已为 {group.id} 进行初始化配置")
        save_config()


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def atrep(app: GraiaMiraiApplication, group: Group, message: MessageChain, member: Member, source: Source):
    ifat = message.has(At)
    if ifat:
        ifa = message.get(At)[0].target == yaml_data['Basic']['MAH']['BotQQ']
        ifas = message.asDisplay().strip(
        ) == f"@{str(yaml_data['Basic']['MAH']['BotQQ'])}"
        if ifas:
            if ifa:
                if member.id == yaml_data['Basic']['Permission']['Master']:
                    await app.sendGroupMessage(group, MessageChain.create([
                        Plain(f"爹！")
                    ]), quote=source.id)
                else:
                    await app.sendGroupMessage(group, MessageChain.create([
                        Plain(f"我是{yaml_data['Basic']['Permission']['MasterName']}"),
                        Plain(f"的机器人{yaml_data['Basic']['BotName']}，"),
                        Plain(f"如果有需要可以联系主人QQ”{str(yaml_data['Basic']['Permission']['Master'])}“，"),
                        Plain(f"添加{yaml_data['Basic']['BotName']}好友后可以被拉到其他群（她会自动同意的），"),
                        Plain(f"{yaml_data['Basic']['BotName']}被群禁言后会自动退出该群。")
                    ]))


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def adminmain(app: GraiaMiraiApplication, group: Group, message: MessageChain):
    if message.asDisplay() in ["/help", "帮助", "菜单"]:
        await app.sendGroupMessage(group, MessageChain.create([Plain(f"{yaml_data['Basic']['BotName']} 使用指南"),
                                                               Plain(f"\n（使用指南还没写，别急。急着需要可以去GitHub"),
                                                               Plain(f"\nhttps://github.com/djkcyl/ABot-Graia"),
                                                               Plain(f"\n发送 <管理员功能菜单> 即可调整群内功能是否开启")]))


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("管理员功能菜单")]))
async def adminmain(app: GraiaMiraiApplication, group: Group, member: Member):
    if member.permission in [MemberPerm.Administrator, MemberPerm.Owner] or member.id in yaml_data['Basic']['Permission']['Admin']:
        msg = []
        msg.append(Plain(f"机器人群管理菜单\n===================\n当前有以下功能可以调整："))
        i = 1
        for func in funcList:
            funcname = func["name"]
            funckey = func["key"]
            funcGlobalDisabled = yaml_data["Saya"][funckey]["Disabled"]
            funcGroupDisabledList = func["key"] in group_data[group.id]["DisabledFunc"]
            if funcGlobalDisabled:
                statu = "全局关闭"
            elif funcGroupDisabledList:
                statu = "本群关闭"
            else:
                statu = "本群开启"
            msg.append(Plain(f"\n{str(i)}.{funcname}：{statu}"))
            i += 1
        msg.append(Plain(f"\n===================\n开启功能/关闭功能 <功能id>\n更多功能待开发，如有特殊需求可以向 {yaml_data['Basic']['Permission']['Master']} 询问"))
        await app.sendGroupMessage(group, MessageChain.create(msg))
    else:
        await app.sendGroupMessage(group, MessageChain.create([Plain(f"你没有使用该功能的权限")]))


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("开启功能")]))
async def onAoff(app: GraiaMiraiApplication, group: Group, member: Member, message: MessageChain):
    if member.permission in [MemberPerm.Administrator, MemberPerm.Owner] or member.id in yaml_data['Basic']['Permission']['Admin']:
        saying = message.asDisplay().split()
        sayfunc = int(saying[1]) - 1
        func = funcList[sayfunc]
        funcname = func["name"]
        funckey = func["key"]
        funcGlobalDisabled = yaml_data["Saya"][funckey]["Disabled"]
        funcGroupDisabled = func["key"] in group_data[group.id]["DisabledFunc"]
        funcDisabledList = group_data[group.id]["DisabledFunc"]
        if funcGlobalDisabled:
            await app.sendGroupMessage(group, MessageChain.create([Plain(f"{funcname}当前处于全局禁用状态")]))
        elif funcGroupDisabled:
            funcDisabledList.remove(funckey)
            group_data[group.id]["DisabledFunc"] = funcDisabledList
            save_config()
            await app.sendGroupMessage(group, MessageChain.create([Plain(f"{funcname}已开启")]))
        else:
            await app.sendGroupMessage(group, MessageChain.create([Plain(f"{funcname}已处于开启状态")]))
    else:
        await app.sendGroupMessage(group, MessageChain.create([Plain(f"你没有使用该功能的权限")]))


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("关闭功能")]))
async def onAoff(app: GraiaMiraiApplication, group: Group, member: Member, message: MessageChain):
    if member.permission in [MemberPerm.Administrator, MemberPerm.Owner] or member.id in yaml_data['Basic']['Permission']['Admin']:
        saying = message.asDisplay().split()
        sayfunc = int(saying[1]) - 1
        func = funcList[sayfunc]
        funcname = func["name"]
        funckey = func["key"]
        funcDisabledList = group_data[group.id]["DisabledFunc"]
        funcGroupDisabled = func["key"] in funcDisabledList
        print(funcGroupDisabled)
        print(group_data[group.id]["DisabledFunc"])
        if not funcGroupDisabled:
            funcDisabledList.append(funckey)
            group_data[group.id]["DisabledFunc"] = funcDisabledList
            save_config()
            await app.sendGroupMessage(group, MessageChain.create([Plain(f"{funcname}已关闭")]))
        else:
            await app.sendGroupMessage(group, MessageChain.create([Plain(f"{funcname}已处于关闭状态")]))
    else:
        await app.sendGroupMessage(group, MessageChain.create([Plain(f"你没有使用该功能的权限")]))
