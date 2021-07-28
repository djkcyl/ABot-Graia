import asyncio
import random
import time

from graia.application import GraiaMiraiApplication
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.event.messages import GroupMessage, FriendMessage
from graia.application.group import Group, Member, MemberPerm
from graia.application.friend import Friend
from graia.application.message.elements.internal import MessageChain, Source, At, Plain, Image_UnsafeBytes
from graia.application.message.parser.literature import Literature

from config import save_config, yaml_data, group_data, black_list
from text2image import create_image

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
    {"name": "有点涩的聊天", "key": "ChatMS"},
    {"name": "没啥用的回复", "key": "Message"},
    {"name": "每日早报", "key": "DailyNewspaper"},
    {"name": "色图", "key": "Setu"},
    {"name": "防撤回", "key": "AnitRecall"}
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

funcHelp = {
    "阿里云tts": {
        "instruction": "将文字转为音频以语音形式发出",
        "usage": "发送指令：\n/tts <语音模型> <文字>",
        "options": "语音模型：男 / 女 / 童 / 日 / 美\n文字：任意180字以内文字"
    },
    "小鸡词典查梗": {
        "instruction": "在小鸡词典内查询梗详情",
        "usage": "发送指令：\n查梗 <梗>",
        "options": "梗：任意可能为梗的文字"
    },
    "小鸡词典emoji转换": {
        "instruction": "吧文字转换为emoji表情",
        "usage": "发送指令：\nemoji <文字>",
        "options": "文字：任意可能被转换为emoji的文字"
    },
    "汉语词典查询": {
        "instruction": "在汉语词典内查询词条",
        "usage": "发送指令：\n词典 <词条>",
        "options": "词条：任意可能存在于词典内的文字"
    },
    "网易云音乐点歌": {
        "instruction": "在网易云音乐搜歌并以语音形式发出",
        "usage": "发送指令：\n点歌",
        "options": "无"
    },
    "网络黑话翻译": {
        "instruction": "翻译类似‘nmsl’一类的简写词",
        "usage": "发送指令：\n你在说什么 <简写>",
        "options": "简写：任意可能为简写词的字母"
    },
    "词云": {
        "instruction": "记录并生成群内词云",
        "usage": "发送指令：\n我的月内总结\n我的年内总结\n本群月内总结\n本群年内总结",
        "options": "无"
    },
    "禁言套餐": {
        "instruction": "随机抽取时长禁言",
        "usage": "发送指令：\n我要禁言套餐",
        "options": "算法为：基本时长x基本倍数=最终时长，有概率触发超级加倍（最终时长加n倍），有极小概率触发头奖（固定30天）"
    },
    "兽语转换": {
        "instruction": "将明文转换为密文或将密文转换为明文",
        "usage": "发送指令：\n嗷 <明文>\n呜 <密文>",
        "options": "明文：任意200字以内文字\n密文：任意被加密后的明文"
    },
    "我的世界服务器Ping": {
        "instruction": "Minecraft 服务器motd获取",
        "usage": "发送指令：\n/mcping <服务器地址>",
        "options": "服务器地址：任意可以正常连接的Java版Minecraft服务器地址"
    },
    "摸头": {
        "instruction": "PetPet",
        "usage": "发送指令：\n摸头<@xxx>\n[戳一戳]xxx",
        "options": "@xxx：@任意本群群友"
    },
    "风格logo生成": {
        "instruction": "生成三种风格化的图片",
        "usage": "发送指令：\nph <文字> <文字>\nyt <文字> <文字>\n5000兆 <文字> <文字>",
        "options": "文字：任意24字以内的文字（建议）"
    },
    "复读姬": {
        "instruction": "人类的本质",
        "usage": "触发条件：\n某条消息重复超过3次\n随机复读某条消息",
        "options": "无"
    },
    "涩图": {
        "instruction": "随机发送P站涩图",
        "usage": "发送指令：\n涩图\n色图\n瑟图\nsetu",
        "options": "无"
    },
    "有点涩的聊天": {
        "instruction": "调用词库进行回复",
        "usage": "发送指令：\n@ABot<文字>",
        "options": "文字：任意可能被回复的文字"
    },
    "没啥用的回复": {
        "instruction": "氛围组！",
        "usage": "无",
        "options": "当前可触发：\n草\n好耶\n流汗黄豆.jpg"
    },
    "每日早报": {
        "instruction": "明天早上八点发送新闻",
        "usage": "每日自动触发",
        "options": "无"
    },
    "色图": {
        "instruction": "随机生成色图",
        "usage": "发送指令：\n涩图\n色图\n瑟图\nsetu",
        "options": "无"
    },
    "防撤回": {
        "instruction": "防止群内消息撤回",
        "usage": "收到撤回事件自动触发",
        "options": "不会防止撤回的有：机器人被撤回的消息、语音、闪照、Xml消息、Json消息"
    }
}


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def atrep(app: GraiaMiraiApplication, group: Group, message: MessageChain, member: Member, source: Source):
    ifat = message.has(At)
    if ifat:
        ifa = message.get(At)[0].target == yaml_data['Basic']['MAH']['BotQQ']
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
                    Plain(f"添加{yaml_data['Basic']['BotName']}好友后请私聊说明用途后即可拉进其他群，主人看到后会选择是否同意入群"),
                    Plain(f"\n{yaml_data['Basic']['BotName']}被群禁言后会自动退出该群。"),
                    Plain(f"\n发送 <菜单> 可以查看功能列表"),
                    Plain(f"\n拥有管理员以上权限可以使用 <管理员功能菜单> 来开关功能"),
                    Plain(f"\n如果用不明白菜单功能可以不用，建议去医院多看看"),
                    Plain(f"\n\n@不会触发任何功能"),
                    Plain(f"\n@不会触发任何功能"),
                    Plain(f"\n@不会触发任何功能")
                ]))


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def adminmain(app: GraiaMiraiApplication, group: Group, message: MessageChain):
    if message.asDisplay() in [".help", "/help", "help", "帮助", "菜单", "功能"]:
        funcusage = []
        for usage in funcHelp:
            funcusage.append(str(f"{usage}：\n" +
                                 funcHelp[usage]["instruction"] + "\n          >>> 用法 >>>\n" +
                                 funcHelp[usage]["usage"] + "\n         >>> 注意事项 >>>\n" +
                                 funcHelp[usage]["options"]))
        help = str(f"{yaml_data['Basic']['BotName']} 使用指南\n\n============================\n")
        help = help + "\n\n----------------------------\n\n".join(funcusage)
        help = help + str(f"\n============================\n" +
                          f"\n所有功能均无需@机器人本身，<x>为可替内容" +
                          f"\n如果用不明白菜单功能可以不用，建议去医院多看看" +
                          f"\n方舟玩家可以加个好友，[官服 A60#6660]" +
                          f"\n可以先试试新制作的 <废物证申请> 一起来成为废物吧~（" +
                          f"\n源码：github.com/djkcyl/ABot-Graia" +
                          f"\n发送 <管理员功能菜单> 即可调整群内功能是否开启")
        image = await create_image(help)
        await app.sendGroupMessage(group, MessageChain.create([Image_UnsafeBytes(image.getvalue())]))


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("管理员功能菜单")]))
async def adminmain(app: GraiaMiraiApplication, group: Group, member: Member):
    if member.permission in [MemberPerm.Administrator, MemberPerm.Owner] or member.id in yaml_data['Basic']['Permission']['Admin']:
        msg = "机器人群管理菜单\n===================\n当前有以下功能可以调整："
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
            msg += f"\n{str(i)}.{funcname}：{statu}"
            i += 1
        msg += str(f"\n===================\n开启功能/关闭功能 <功能id> " +
                   f"\n如果用不明白菜单功能可以不用，建议去医院多看看" +
                   f"\n更多功能待开发，如有特殊需求可以向 {yaml_data['Basic']['Permission']['Master']} 询问")
        image = await create_image(msg)
        await app.sendGroupMessage(group, MessageChain.create([Image_UnsafeBytes(image.getvalue())]))
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
        if not funcGroupDisabled:
            funcDisabledList.append(funckey)
            group_data[group.id]["DisabledFunc"] = funcDisabledList
            save_config()
            await app.sendGroupMessage(group, MessageChain.create([Plain(f"{funcname}已关闭")]))
        else:
            await app.sendGroupMessage(group, MessageChain.create([Plain(f"{funcname}已处于关闭状态")]))
    else:
        await app.sendGroupMessage(group, MessageChain.create([Plain(f"你没有使用该功能的权限")]))


@channel.use(ListenerSchema(listening_events=[FriendMessage], inline_dispatchers=[Literature("公告")]))
async def Announcement(app: GraiaMiraiApplication, friend: Friend, message: MessageChain):
    if friend.id == yaml_data['Basic']['Permission']['Master']:
        ft = time.time()
        saying = message.asDisplay().split(" ", 1)
        if len(saying) == 2:
            image = await create_image(saying[1])
            groupList = await app.groupList()
            for group in groupList:
                if group.id not in [885355617, 780537426, 474769367]:
                    await app.sendGroupMessage(group.id, MessageChain.create([
                        Plain(f"公告：{str(group.id)}\n"),
                        Image_UnsafeBytes(image.getvalue())
                    ]))
                    await asyncio.sleep(random.randint(3, 5))
            tt = time.time()
            times = str(tt - ft)
            await app.sendFriendMessage(friend, MessageChain.create(f"群发已完成，耗时 {times} 秒"))


@channel.use(ListenerSchema(listening_events=[FriendMessage], inline_dispatchers=[Literature("拉黑群聊")]))
async def Announcement(app: GraiaMiraiApplication, friend: Friend, message: MessageChain):
    if friend.id == yaml_data['Basic']['Permission']['Master']:
        saying = message.asDisplay().split()
        if len(saying) == 2:
            groupBlackList = black_list['group']
            if int(saying[1]) in groupBlackList:
                await app.sendFriendMessage(friend, MessageChain.create([Plain(f"该群已被拉黑")]))
            else:
                groupBlackList.append(int(saying[1]))
                black_list['group'] = groupBlackList
                save_config()
                await app.sendGroupMessage(int(saying[1]), MessageChain.create([Plain(f"该群已进入黑名单，将在3秒后退出")]))
                await asyncio.sleep(3)
                await app.quit(int(saying[1]))
                await app.sendFriendMessage(friend, MessageChain.create([Plain(f"成功拉黑该群")]))
