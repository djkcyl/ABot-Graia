import time

from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.parser.pattern import RegexMatch
from graia.ariadne.message.parser.literature import Literature
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.element import Quote, At, Plain, Image
from graia.ariadne.message.parser.twilight import Twilight, Sparkle


from util.text2image import create_image
from util.control import Permission, Interval
from util.sendMessage import selfSendGroupMessage
from config import save_config, yaml_data, group_data

saya = Saya.current()
channel = Channel.current()


funcList = [
    {"name": "微软文字转语音", "key": "AzureTTS", "can_disabled": True, "default_disabled": False},
    {"name": "小鸡词典查梗", "key": "ChickDict", "can_disabled": True, "default_disabled": False},
    {"name": "小鸡词典emoji转换", "key": "ChickEmoji", "can_disabled": True, "default_disabled": False},
    {"name": "汉语词典查询", "key": "ChineseDict", "can_disabled": True, "default_disabled": False},
    {"name": "网易云音乐点歌", "key": "CloudMusic", "can_disabled": True, "default_disabled": False},
    {"name": "网络黑话翻译", "key": "CyberBlacktalk", "can_disabled": True, "default_disabled": False},
    {"name": "词云", "key": "WordCloud", "can_disabled": True, "default_disabled": False},
    {"name": "禁言套餐", "key": "MutePack", "can_disabled": True, "default_disabled": False},
    {"name": "兽语转换", "key": "Beast", "can_disabled": True, "default_disabled": False},
    {"name": "我的世界服务器Ping", "key": "MinecraftPing", "can_disabled": True, "default_disabled": False},
    {"name": "摸头", "key": "PetPet", "can_disabled": True, "default_disabled": False},
    {"name": "风格logo生成", "key": "StyleLogoGenerator", "can_disabled": True, "default_disabled": False},
    {"name": "复读姬", "key": "Repeater", "can_disabled": True, "default_disabled": False},
    {"name": "涩图", "key": "Pixiv", "can_disabled": True, "default_disabled": False},
    {"name": "有点涩的聊天", "key": "ChatMS", "can_disabled": True, "default_disabled": False},
    {"name": "没啥用的回复", "key": "Message", "can_disabled": True, "default_disabled": False},
    {"name": "每日早报", "key": "DailyNewspaper", "can_disabled": True, "default_disabled": False},
    {"name": "色图", "key": "Setu", "can_disabled": True, "default_disabled": False},
    {"name": "防撤回", "key": "AnitRecall", "can_disabled": True, "default_disabled": False},
    {"name": "娱乐功能", "key": "Entertainment", "can_disabled": True, "default_disabled": False},
    {"name": "骰娘", "key": "DiceMaid", "can_disabled": True, "default_disabled": False},
    {"name": "B站视频解析", "key": "BilibiliResolve", "can_disabled": True, "default_disabled": False},
    {"name": "听歌识曲 / 哼唱识曲", "key": "VoiceMusicRecognition", "can_disabled": True, "default_disabled": False},
    {"name": "淫文翻译机", "key": "Yinglish", "can_disabled": True, "default_disabled": False},
    {"name": "背单词", "key": "EnglishTest", "can_disabled": True, "default_disabled": False},
    {"name": "BiliBili订阅推送", "key": "BilibiliDynamic", "can_disabled": False, "default_disabled": False},
    {"name": "查看人设", "key": "CharacterDesignGenerator", "can_disabled": True, "default_disabled": False},
    {"name": "以图搜番 / 以图搜图", "key": "AnimeSceneSearch", "can_disabled": True, "default_disabled": False},
    {"name": "查战绩", "key": "RecordQuery", "can_disabled": True, "default_disabled": False},
    {"name": "明日方舟蹲饼", "key": "ArkNews", "can_disabled": True, "default_disabled": True},
    {"name": "低多边形图片生成", "key": "LowPolygon", "can_disabled": True, "default_disabled": False},
    {"name": "计算器", "key": "Calculator", "can_disabled": True, "default_disabled": False}

]

configList = [
    {"name": "入群欢迎", "key": "WelcomeMSG"},
    {"name": "退群通知", "key": "LeaveMSG"}
]

DisabledFunc = []
for func in funcList:
    if func['default_disabled']:
        DisabledFunc.append(func['key'])

groupInitData = {
    "DisabledFunc": DisabledFunc,
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
        "usage": "发送指令：\n查看个人词云\n查看本群词云",
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
        "instruction": "明天早上八点半发送新闻",
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
        "usage": "发送指令：\n签到\n你画我猜\n赠送游戏币\n查看排行榜",
        "options": "签到：每日凌晨四点重置签到，每次签到可获得 5-21 个游戏币\n你画我猜：每次消耗 4 个游戏币\n  赠送游戏币：可以向他人赠送自己的游戏币，限值 1-1000以内\n排行榜可同时查看游戏币榜和发言榜，一般情况下排行榜每十分钟更新一次",
        "example": "  赠送游戏币 @ABot 15"
    },
    "骰娘": {
        "instruction": "一个简易骰娘",
        "usage": "发送指令：\n.r",
        "options": "可选参数有：\nr ==> 投掷的骰子个数\nd ==> 每个骰子的面数\nk ==> 取最大的前n个\n以上三个参数除 r 外均为可选参数\n如未填写的情况下：\nr 默认值为1\nd 默认值为100\nk 默认值为0（即不取最大）",
        "example": ".r  投掷1个骰子，最大值为100\n.rd50  投掷1个骰子，最大值为50\n.r3d6  投掷3个骰子，每个的最大值为6\n.r15k4  投掷15个骰子，每个的最大值为100，取最大的前4个"
    },
    "B站视频解析": {
        "instruction": "全自动B站链接解析",
        "usage": "收到任意带有B站链接的消息，av号、BV号、b23短链、小程序等",
        "options": "无",
        "example": "（这也需要示例吗？"
    },
    "听歌识曲 / 哼唱识曲": {
        "instruction": "和音乐软件一样的听歌识曲、哼唱识曲",
        "usage": "发送指令：\n识曲 <模式>",
        "options": "模式：原曲、哼唱\n可选择听歌识曲或哼唱识曲，每使用一次无论成功与否均会消耗 2 个游戏币",
        "example": "识曲 原曲"
    },
    "淫文翻译机": {
        "instruction": "能把中文翻译成淫语的翻译机！",
        "usage": "发送指令：\n淫语 <文字>",
        "options": "文字：任意100字以内的文字（建议）",
        "example": "淫语 不行，那里不行"
    },
    "背单词": {
        "instruction": "字面意思",
        "usage": "发送指令：\n背单词",
        "options": "发送背单词后选择想要学习的词库，机器人将会发题，请根据题目作答，15秒后未作答将提供三次提示，答题系统为全群共享，即“一人开启，全群皆可作答”，如果不想学或者想更换题库可发送取消来终止进程。\n（本功能支持私聊使用）",
        "example": "（这也需要示例吗？"
    },
    "BiliBili订阅推送": {
        "instruction": "自动推送b站的动态及直播间更新",
        "usage": "发送指令：\n订阅 <uid>\n退订 <uid>\n本群订阅列表",
        "options": "如果不知道uid怎么获得，请去百度！订阅和退订的指令仅有群管理及以上权限可用",
        "example": "订阅 161775300"
    },
    "查看人设": {
        "instruction": "通过seed随机出人设表",
        "usage": "发送指令：\n查看人设",
        "options": "发送查看人设之后会根据群号和qq号随机出一个人设表，在不同的群里随机到的数据都不一样哦",
        "example": "（这也需要示例吗？"
    },
    "以图搜番 / 以图搜图": {
        "instruction": "发送图片来搜索出处",
        "usage": "发送指令：\n以图搜番\n以图搜图",
        "options": "清晰度太低的图可能搜不到，无论成功与否均会扣除 4 个游戏币",
        "example": "（这也需要示例吗？"
    },
    "查战绩": {
        "instruction": "用来查询所支持游戏的玩家战绩",
        "usage": "发送指令：\n查战绩",
        "options": "目前可以查询 “彩虹六号：围攻”\n首次输入需要绑定游戏id，可以at其他已绑定的人查询，也可以直接输入id查询",
        "example": "查战绩 r6\n查战绩 r6 @xxxx\n查战绩 r6 Eustiana"
    },
    "明日方舟蹲饼": {
        "instruction": "自动群发明日方舟微博和游戏内公告",
        "usage": "无",
        "options": "本功能默认关闭，如需使用请自行开启。",
        "example": "无"
    },
    "低多边形图片生成": {
        "instruction": "吧图片转换为低多边形风格化",
        "usage": "发送指令：\n低多边形",
        "options": "图片越大生成越慢，请耐心等待",
        "example": "（这也需要示例吗？"
    },
    "计算器": {
        "instruction": "一个只支持 “加减乘除()” 的计算器功能",
        "usage": "发送指令：\n计算器 <式子>",
        "options": "只支持 加！减！乘！除！！！",
        "example": "计算器 60+2*(-3-40.0+42425/5)*(9-2*5/3)"
    },
}


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            decorators=[Permission.require()]))
async def atrep(app: Ariadne, group: Group, message: MessageChain):
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
            msg = Plain("Zzzzzz~")
        else:
            image = await create_image(str(
                f"我是{yaml_data['Basic']['Permission']['MasterName']}" +
                f"的机器人{yaml_data['Basic']['BotName']}" +
                f"\n如果有需要可以联系主人QQ”{str(yaml_data['Basic']['Permission']['Master'])}“，" +
                f"\n邀请 {yaml_data['Basic']['BotName']} 加入其他群需先询问主人获得白名单" +
                f"\n{yaml_data['Basic']['BotName']} 被群禁言后会自动退出该群。" +
                "\n发送 <菜单> 可以查看功能列表" +
                "\n@不会触发任何功能　　　　@不会触发任何功能" +
                "\n@不会触发任何功能　　　　@不会触发任何功能" +
                "\n@不会触发任何功能　　　　@不会触发任何功能" +
                "\n@不会触发任何功能　　　　@不会触发任何功能" +
                "\n@不会触发任何功能　　　　@不会触发任何功能" +
                "\n@不会触发任何功能　　　　@不会触发任何功能"))
            msg = Image(data_bytes=image)
        await selfSendGroupMessage(group, MessageChain.create([msg]))


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Literature("功能")],
                            decorators=[Permission.require(), Interval.require(5)]))
async def funchelp(app: Ariadne, group: Group, message: MessageChain):
    saying = message.asDisplay().split()
    if len(saying) == 2:
        sayfunc = funcList[int(saying[1]) - 1]['name']
        funckey = funcList[int(saying[1]) - 1]['key']
        funcGlobalDisabled = yaml_data["Saya"][funckey]["Disabled"]
        funcGroupDisabledList = funckey in group_data[str(group.id)]["DisabledFunc"]
        if funcGlobalDisabled or funcGroupDisabledList:
            return await selfSendGroupMessage(group, MessageChain.create([
                Plain("该功能暂不开启")
            ]))
        help = str(sayfunc +
                   "\n\n      >>> 用法 >>>\n" +
                   funcHelp[sayfunc]["usage"] +
                   "\n\n      >>> 注意事项 >>>\n" +
                   funcHelp[sayfunc]["options"] +
                   "\n\n      >>> 示例 >>>\n" +
                   funcHelp[sayfunc]["example"]
                   )
        image = await create_image(help)
        await selfSendGroupMessage(group, MessageChain.create([Image(data_bytes=image)]))
    else:
        await selfSendGroupMessage(group, MessageChain.create([Plain("请输入 功能 <id>，如果不知道id可以发送菜单查看")]))


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Twilight(Sparkle([RegexMatch(r'^[。./]?help$|^帮助$|^菜单$')]))],
                            decorators=[Permission.require()]))
async def help(app: Ariadne, group: Group):
    msg = f"{yaml_data['Basic']['BotName']} 群菜单 / {str(group.id)}\n{group.name}\n========================================================"
    i = 1
    for func in funcList:
        funcname = func["name"]
        funckey = func["key"]
        funcGlobalDisabled = yaml_data["Saya"][funckey]["Disabled"]
        funcGroupDisabledList = func["key"] in group_data[str(group.id)]["DisabledFunc"]
        if funcGlobalDisabled:
            statu = "【全局关闭】"
        elif funcGroupDisabledList:
            statu = "【  关闭  】"
        else:
            statu = "            "
        if i < 10:
            si = " " + str(i)
        else:
            si = str(i)
        msg += f"\n{si}  {statu}  {funcname}"
        i += 1
    msg += str("\n========================================================" +
               "\n管理员可发送 开启功能/关闭功能 <id>，例如：关闭功能 1" +
               "\n详细查看功能使用方法请发送 功能 <id>，例如：功能 1" +
               "\n管理员可发送 开启功能/关闭功能 <功能id> " +
               "\n每日00:00至07:30为休息时间，将关闭大部分功能" +
               "\n所有功能均无需@机器人本身" +
               "\n方舟玩家可以加个好友，[官服 A60#6660]" +
               "\n源码：github.com/djkcyl/ABot-Graia" +
               f"\n更多功能待开发，如有特殊需求可以向 {yaml_data['Basic']['Permission']['Master']} 询问")
    image = await create_image(msg, 80)
    await selfSendGroupMessage(group, MessageChain.create([Image(data_bytes=image)]))


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Literature("开启功能")],
                            decorators=[Permission.require(Permission.GROUP_ADMIN), Interval.require(5)]))
async def on_func(app: Ariadne, group: Group, message: MessageChain):
    saying = message.asDisplay().split()
    sayfunc = int(saying[1]) - 1
    func = funcList[sayfunc]
    funcname = func["name"]
    funckey = func["key"]
    funcGlobalDisabled = yaml_data["Saya"][funckey]["Disabled"]
    funcGroupDisabled = func["key"] in group_data[str(group.id)]["DisabledFunc"]
    funcDisabledList = group_data[str(group.id)]["DisabledFunc"]
    if funcGlobalDisabled:
        await selfSendGroupMessage(group, MessageChain.create([Plain(f"{funcname}当前处于全局禁用状态")]))
    elif funcGroupDisabled:
        funcDisabledList.remove(funckey)
        group_data[str(group.id)]["DisabledFunc"] = funcDisabledList
        save_config()
        await selfSendGroupMessage(group, MessageChain.create([Plain(f"{funcname}已开启")]))
    else:
        await selfSendGroupMessage(group, MessageChain.create([Plain(f"{funcname}已处于开启状态")]))


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Literature("关闭功能")],
                            decorators=[Permission.require(Permission.GROUP_ADMIN), Interval.require(5)]))
async def off_func(app: Ariadne, group: Group, message: MessageChain):
    saying = message.asDisplay().split()
    sayfunc = int(saying[1]) - 1
    func = funcList[sayfunc]
    funcname = func["name"]
    funckey = func["key"]
    funcCanDisabled = func["can_disabled"]
    funcDisabledList = group_data[str(group.id)]["DisabledFunc"]
    funcGroupDisabled = func["key"] in funcDisabledList
    if not funcCanDisabled:
        await selfSendGroupMessage(group, MessageChain.create([Plain(f"{funcname}无法被关闭")]))
    elif not funcGroupDisabled:
        funcDisabledList.append(funckey)
        group_data[str(group.id)]["DisabledFunc"] = funcDisabledList
        save_config()
        await selfSendGroupMessage(group, MessageChain.create([Plain(f"{funcname}已关闭")]))
    else:
        await selfSendGroupMessage(group, MessageChain.create([Plain(f"{funcname}已处于关闭状态")]))
