from graia.application import GraiaMiraiApplication
from graia.application.event.messages import Group
from graia.application.message.elements.internal import MessageChain, Plain


async def sendmsg(app: GraiaMiraiApplication, group: Group):
    await app.sendGroupMessage(group, MessageChain.create([Plain("该功能暂不开启")]))


class Config:
    class Basic:  # 基础配置
        BotName = str("")  # 机器人在群里的名字

        class MAH:  # Mirai HTTP API配置
            BotQQ = int()  # 机器人QQ号
            MiraiHost = str("")  # Mirai HTTP API地址
            MiraiAuthKey = str("")  # Mirai HTTP API AuthKey

        class Permission:  # 权限管理
            Master = int()  # 机器人主人QQ号
            MasterName = str("")  # 机器人主人昵称
            Admin = list([  # 机器人管理员
                Master,
            ])

    class Saya:  # saya 插件配置
        class AliTTS:  # 阿里云文字转语音
            Disabled = bool(False)  # 是否禁用
            Blacklist = list([  # 禁用的群
                
            ])
            # API申请地址：https://nls-portal.console.aliyun.com
            Appkey = str("")

            class AccessKey:  # AccessKey 获取地址：https://help.aliyun.com/document_detail/69835.htm
                Id = str("")
                Secret = str("")

        class ChickDict:  # 小鸡词典
            Disabled = bool(False)  # 是否禁用
            Blacklist = list([  # 禁用的群

            ])

        class ChickEmoji:  # 小鸡词典emoji翻译
            Disabled = bool(False)  # 是否禁用
            Blacklist = list([  # 禁用的群

            ])

        class ChineseDict:  # 汉典
            Disabled = bool(False)  # 是否禁用
            Blacklist = list([  # 禁用的群

            ])

        class CloudMusic:  # 网易云音乐点歌
            Disabled = bool(False)  # 是否禁用
            Blacklist = list([  # 禁用的群

            ])
            MusicInfo = bool(True)  # 是否发送音乐信息

        class CloudMusic:  # 网易云音乐点歌
            Disabled = bool(False)  # 是否禁用
            Blacklist = list([  # 禁用的群

            ])

            class ApiConfig:  # Api搭建：https://github.com/Binaryify/NeteaseCloudMusicApi
                PhoneNumber = str()  # 登录手机号码
                Password = str("")  # 登录密码

        class WordCloud:  # 词云生成
            Disabled = bool(False)  # 是否禁用
            Blacklist = list([  # 禁用的群

            ])

        class MutePack:  # 禁言套餐
            Disabled = bool(False)  # 是否禁用
            Blacklist = list([  # 禁用的群
                
            ])
            MaxTime = int(3000)  # 单倍最大时长
            MaxMultiple = int(8)  # 最大基础倍数
            MaxJackpotProbability = int(10000)  # 头奖概率 x分之一
            SuperDouble = bool(True)  # 是否开启超级加倍
            MaxSuperDoubleProbability = int(25)  # 超级加倍概率 x分之一
            MaxSuperDoubleMultiple = int(12)  # 超级加倍最大倍数

        class Beast:  # 兽语转换
            Disabled = bool(False)  # 是否禁用
            Blacklist = list([  # 禁用的群

            ])
            BeastPhrase = list(['嗷', '呜', '啊', '~'])  # 兽语字符组，需要填写四个字符

        class MinecraftPing:  # Minecraft Server PING
            Disabled = bool(False)  # 是否禁用
            Blacklist = list([  # 禁用的群

            ])

        class PetPet:  # 摸头 GIF 生成
            Disabled = bool(False)  # 是否禁用
            Blacklist = list([  # 禁用的群

            ])
            CanAt = bool(True)  # 是否可通过消息 at 触发
            CanNudge = bool(True)  # 是否可通过戳一戳触发

        class PornhubLogo:  # Pornhub Logo 生成
            Disabled = bool(False)  # 是否禁用
            Blacklist = list([  # 禁用的群

            ])

    Final = bool(False)  # 配置完成后请调整为 True


if not Config.Final:
    print("配置文件未修改完成，请手动编辑 config.py 进行修改")
    exit()
