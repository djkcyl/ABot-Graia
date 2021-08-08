import time
import random
import asyncio

from graia.saya import Saya, Channel
from graia.application.friend import Friend
from graia.application import GraiaMiraiApplication
from graia.application.exceptions import UnknownTarget
from graia.application.group import Group, Member, MemberPerm
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.parser.literature import Literature
from graia.application.event.messages import GroupMessage, FriendMessage
from graia.application.message.elements.internal import MessageChain, Quote, At, Plain, Image_UnsafeBytes

from config import save_config, yaml_data, group_data, group_list
from util.text2image import create_image
from util.RestControl import set_sleep

saya = Saya.current()
channel = Channel.current()


funcList = [
    {"name": "微软文字转语音", "key": "AzureTTS"},
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
    {"name": "防撤回", "key": "AnitRecall"},
    {"name": "娱乐功能", "key": "Entertainment"},
    {"name": "骰娘", "key": "DiceMaid"}
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
    "微软文字转语音": {
        "instruction": "将文字转为音频以语音形式发出",
        "usage": "发送指令：\n/tts <性别> <感情> <文字>",
        "options": "性别：男 / 女\n感情：\n当性别为男时：【助理、平静、害怕、开心、不满、严肃、生气、悲伤、沮丧、尴尬、默认】\n当性别为女时：【助理、聊天、客服、新闻、撒娇、生气、平静、开心、不满、害怕、温柔、抒情、悲伤、严肃、默认】\n文字：任意600字以内文字\n请求语音需要消耗 2 个游戏币",
        "example": "/tts 男 助理 您好，您的外卖到了，请您开下门"
    },
    "小鸡词典查梗": {
        "instruction": "在小鸡词典内查询梗详情",
        "usage": "发送指令：\n查梗 <梗>",
        "options": "梗：任意可能为梗的文字",
        "example": "查梗 两面包夹芝士"
    },
    "小鸡词典emoji转换": {
        "instruction": "吧文字转换为emoji表情",
        "usage": "发送指令：\nemoji <文字>",
        "options": "文字：任意可能被转换为emoji的文字",
        "example": "emoji 差不多的了"
    },
    "汉语词典查询": {
        "instruction": "在汉语词典内查询词条",
        "usage": "发送指令：\n词典 <词条>",
        "options": "词条：任意可能存在于词典内的文字",
        "example": "词典 对牛弹琴"
    },
    "网易云音乐点歌": {
        "instruction": "在网易云音乐搜歌并以语音形式发出",
        "usage": "发送指令：\n点歌",
        "options": "可以点需要黑胶VIP的歌曲，每次点歌消耗 4 个游戏币",
        "example": "点歌\n点歌 梦于星海之间"
    },
    "网络黑话翻译": {
        "instruction": "翻译类似‘nmsl’一类的简写词",
        "usage": "发送指令：\n你在说什么 <简写>",
        "options": "简写：任意可能为简写词的字母",
        "example": "你在说什么 jyfm"
    },
    "词云": {
        "instruction": "记录并生成群内词云",
        "usage": "发送指令：\n我的月内总结\n我的年内总结\n本群月内总结\n本群年内总结",
        "options": "无",
        "example": "（这也需要示例吗？"
    },
    "禁言套餐": {
        "instruction": "随机抽取时长禁言",
        "usage": "发送指令：\n我要禁言套餐",
        "options": "算法为：基本时长x基本倍数=最终时长，有概率触发超级加倍（最终时长加n倍），有极小概率触发头奖（固定30天）",
        "example": "（这也需要示例吗？"
    },
    "兽语转换": {
        "instruction": "将明文转换为密文或将密文转换为明文",
        "usage": "发送指令：\n嗷 <明文>\n呜 <密文>",
        "options": "明文：任意200字以内文字\n密文：任意被加密后的明文",
        "example": "嗷 你好\n呜 呜嗷嗷嗷啊嗷嗷~啊呜~啊~呜呜嗷"
    },
    "我的世界服务器Ping": {
        "instruction": "Minecraft 服务器motd获取",
        "usage": "发送指令：\n/mcping <服务器地址>",
        "options": "服务器地址：任意可以正常连接的Java版Minecraft服务器地址",
        "example": "/mcping mc.hypixel.net"
    },
    "摸头": {
        "instruction": "生成摸头gif",
        "usage": "发送指令：\n摸头 <@xxx>\n[戳一戳]xxx",
        "options": "@xxx：@任意本群群友",
        "example": "摸头 @ABot\n（戳一戳也需要示例吗？"
    },
    "风格logo生成": {
        "instruction": "生成三种风格化的图片",
        "usage": "发送指令：\nph <文字> <文字>\nyt <文字> <文字>\n5000兆 <文字> <文字>",
        "options": "文字：任意24字以内的文字（建议）",
        "example": "ph 我是 ABot\nyt 我是 ABot\n5000兆 我是 ABot"
    },
    "复读姬": {
        "instruction": "人类的本质",
        "usage": "触发条件：\n某条消息重复超过3次\n随机复读某条消息",
        "options": "无",
        "example": "（这也需要示例吗？"
    },
    "涩图": {
        "instruction": "随机发送P站涩图",
        "usage": "发送指令：\n涩图\n色图\n瑟图\nsetu",
        "options": "由于近期腾讯严查，GHS封号比较频繁，再加上举报的内鬼太多了，涩图功能就先不开了，过段时间看情况再开",
        "example": "（这也需要示例吗？"
    },
    "有点涩的聊天": {
        "instruction": "调用词库进行回复",
        "usage": "发送指令：\n@ABot<文字>",
        "options": "文字：任意可能被回复的文字",
        "example": "（这也需要示例吗？"
    },
    "没啥用的回复": {
        "instruction": "氛围组！",
        "usage": "无",
        "options": "当前可触发：\n草\n好耶\n流汗黄豆.jpg",
        "example": "（这也需要示例吗？"
    },
    "每日早报": {
        "instruction": "明天早上八点发送新闻",
        "usage": "每日自动触发",
        "options": "无",
        "example": "（这也需要示例吗？"
    },
    "色图": {
        "instruction": "随机生成色图",
        "usage": "发送指令：\n涩图\n色图\n瑟图\nsetu",
        "options": "无",
        "example": "（这也需要示例吗？"
    },
    "防撤回": {
        "instruction": "防止群内消息撤回",
        "usage": "收到撤回事件自动触发",
        "options": "不会防止撤回的有：机器人被撤回的消息、语音、闪照、Xml消息、Json消息",
        "example": "（这也需要示例吗？"
    },
    "娱乐功能": {
        "instruction": "提供一些群内互动娱乐功能",
        "usage": "发送指令：\n签到\n你画我猜\n购买奖券 | 兑换奖券 | 开奖查询\n转账",
        "options": "签到：每日凌晨四点重置签到，每次签到可获得 2-16 个游戏币\n你画我猜：每次消耗 4 个游戏币\n奖券：奖券每人可不限量购买，每张需要 2 游戏币，每周一00:00开奖。当期开奖的奖券仅可当期兑换，兑换后将扣取10%。奖券请妥善保管，如有丢失一概不补！\n转账：可以向他人转送自己的游戏币，限值 1-1000以内",
        "example": "转账 @ABot 15"
    },
    "骰娘": {
        "instruction": "一个简易骰娘",
        "usage": "发送指令：\n.r",
        "options": "可选参数有：\nr ==> 投掷的骰子个数\nd ==> 每个骰子的面数\nk ==> 取最大的前n个\n以上三个参数除 r 外均为可选参数\n如为填写的情况下：\nr 默认值为1\nd 默认值为100\nk 默认值为0（即不取最大）",
        "example": ".r  投掷1个骰子，最大值为100\n.rd50  投掷1个骰子，最大值为50\n.r3d6  投掷3个骰子，每个的最大值为6\n.r15k4  投掷15个骰子，每个的最大值为100，取最大的前4个"
    }
}


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def atrep(app: GraiaMiraiApplication, group: Group, message: MessageChain):
    if message.has(At):
        ifa = message.get(At)[0].target == yaml_data['Basic']['MAH']['BotQQ']
    else:
        ifa = False
    ifquote = not message.has(Quote)
    ifasdisplay = message.asDisplay().replace(" ", "") == f"@{yaml_data['Basic']['MAH']['BotQQ']}"
    # 判断是否为空消息，判断是否at，判断是否回复
    if ifa and ifasdisplay and ifquote:
        now_localtime = time.strftime("%H:%M:%S", time.localtime())
        if "00:00:00" < now_localtime < "07:30:00":
            msg = [Plain("Zzzzzz~")]
        else:
            image = await create_image(str(
                f"我是{yaml_data['Basic']['Permission']['MasterName']}" +
                f"的机器人{yaml_data['Basic']['BotName']}" +
                f"\n如果有需要可以联系主人QQ”{str(yaml_data['Basic']['Permission']['Master'])}“，" +
                f"\n邀请 {yaml_data['Basic']['BotName']} 加入其他群需先询问主人获得白名单" +
                f"\n{yaml_data['Basic']['BotName']} 被群禁言后会自动退出该群。" +
                f"\n发送 <菜单> 可以查看功能列表" +
                f"\n如果用不明白菜单功能可以不用，建议去医院多看看" +
                f"\n\n@不会触发任何功能　　　　@不会触发任何功能" +
                f"\n@不会触发任何功能　　　　@不会触发任何功能" +
                f"\n@不会触发任何功能　　　　@不会触发任何功能" +
                f"\n@不会触发任何功能　　　　@不会触发任何功能" +
                f"\n@不会触发任何功能　　　　@不会触发任何功能" +
                f"\n@不会触发任何功能　　　　@不会触发任何功能"))
            msg = [Image_UnsafeBytes(image.getvalue())]
        await app.sendGroupMessage(group, MessageChain.create(msg))


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("功能")]))
async def adminmain(app: GraiaMiraiApplication, group: Group, message: MessageChain):
    saying = message.asDisplay().split()
    if len(saying) == 2:
        sayfunc = funcList[int(saying[1]) - 1]['name']
        help = str(sayfunc +
                   "\n\n >>> 用法 >>>\n" +
                   funcHelp[sayfunc]["usage"] +
                   "\n\n >>> 注意事项 >>>\n" +
                   funcHelp[sayfunc]["options"] +
                   "\n\n >>> 示例 >>>\n" +
                   funcHelp[sayfunc]["example"]
                   )
        image = await create_image(help)
        await app.sendGroupMessage(group, MessageChain.create([Image_UnsafeBytes(image.getvalue())]))
    else:
        await app.sendGroupMessage(group, MessageChain.create([[Plain("请输入 功能 <id>，如果不知道id可以发送菜单查看")]]))


@channel.use(ListenerSchema(listening_events=[GroupMessage]))
async def adminmain(app: GraiaMiraiApplication, group: Group, message: MessageChain):
    if message.asDisplay() in [".help", "/help", "help", "帮助", "菜单"]:
        msg = f"{yaml_data['Basic']['BotName']} 群菜单 / {str(group.id)}\n{group.name}\n==============================="
        i = 1
        for func in funcList:
            funcname = func["name"]
            funckey = func["key"]
            funcGlobalDisabled = yaml_data["Saya"][funckey]["Disabled"]
            funcGroupDisabledList = func["key"] in group_data[group.id]["DisabledFunc"]
            if funcGlobalDisabled:
                statu = "【全局关闭】"
            elif funcGroupDisabledList:
                statu = "【本群关闭】"
            else:
                statu = "　　　　　　"
            if i < 10:
                si = "  " + str(i)
            else:
                si = str(i)
            msg += f"\n{si}　{statu}　{funcname}"
            i += 1
        msg += str("\n===============================" +
                   "\n管理员可发送 开启功能/关闭功能 <id>，例如：关闭功能 1" +
                   "\n详细查看功能使用方法请发送 功能 <id>，例如：功能 1" +
                   "\n所有功能均无需@机器人本身" +
                   "\n如果用不明白菜单功能可以不用，建议去医院多看看" +
                   "\n方舟玩家可以加个好友，[官服 A60#6660]" +
                   "\n源码：github.com/djkcyl/ABot-Graia" +
                   "\n管理员可发送 开启功能/关闭功能 <功能id> " +
                   "\n如果用不明白菜单可以不用，建议去医院多看看" +
                   f"\n更多功能待开发，如有特殊需求可以向 {yaml_data['Basic']['Permission']['Master']} 询问")
        image = await create_image(msg)
        await app.sendGroupMessage(group, MessageChain.create([Image_UnsafeBytes(image.getvalue())]))


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
                if group.id not in [885355617, 780537426, 474769367, 690211045, 855895642]:
                    try:
                        await app.sendGroupMessage(group.id, MessageChain.create([
                            Plain(f"公告：{str(group.id)}\n"),
                            Image_UnsafeBytes(image.getvalue())
                        ]))
                    except Exception as err:
                        await app.sendFriendMessage(yaml_data['Basic']['Permission']['Master'], MessageChain.create([
                            Plain(f"{group.id} 的公告发送失败\n{err}")
                        ]))
                    await asyncio.sleep(random.uniform(5, 7))
            tt = time.time()
            times = str(tt - ft)
            await app.sendFriendMessage(friend, MessageChain.create([Plain(f"群发已完成，耗时 {times} 秒")]))


@channel.use(ListenerSchema(listening_events=[FriendMessage], inline_dispatchers=[Literature("添加白名单")]))
async def Announcement(app: GraiaMiraiApplication, friend: Friend, message: MessageChain):
    if friend.id == yaml_data['Basic']['Permission']['Master']:
        saying = message.asDisplay().split()
        if len(saying) == 2:
            if int(saying[1]) in group_list['white']:
                await app.sendFriendMessage(friend, MessageChain.create([Plain(f"该群已在白名单中")]))
            else:
                group_list['white'].append(int(saying[1]))
                save_config()
                await app.sendFriendMessage(friend, MessageChain.create([Plain(f"成功将该群加入白名单")]))


@channel.use(ListenerSchema(listening_events=[FriendMessage], inline_dispatchers=[Literature("取消白名单")]))
async def Announcement(app: GraiaMiraiApplication, friend: Friend, message: MessageChain):
    if friend.id == yaml_data['Basic']['Permission']['Master']:
        saying = message.asDisplay().split()
        if len(saying) == 2:
            if int(saying[1]) not in group_list['white']:
                await app.sendFriendMessage(friend, MessageChain.create([Plain(f"该群未在白名单中")]))
            else:
                group_list['white'].remove(int(saying[1]))
                save_config()
                try:
                    await app.sendGroupMessage(int(saying[1]), MessageChain.create([Plain(f"该群已被移出白名单，将在3秒后退出")]))
                    await asyncio.sleep(3)
                    await app.quit(int(saying[1]))
                except UnknownTarget:
                    pass
                await app.sendFriendMessage(friend, MessageChain.create([Plain(f"成功将该群移出白名单")]))


@channel.use(ListenerSchema(listening_events=[FriendMessage], inline_dispatchers=[Literature("休息")]))
async def Announcement(app: GraiaMiraiApplication, friend: Friend):
    if friend.id == yaml_data['Basic']['Permission']['Master']:
        set_sleep(1)
        await app.sendFriendMessage(friend, MessageChain.create([Plain(f"已进入休息")]))


@channel.use(ListenerSchema(listening_events=[FriendMessage], inline_dispatchers=[Literature("工作")]))
async def Announcement(app: GraiaMiraiApplication, friend: Friend):
    if friend.id == yaml_data['Basic']['Permission']['Master']:
        set_sleep(0)
        await app.sendFriendMessage(friend, MessageChain.create([Plain(f"已开始工作")]))
