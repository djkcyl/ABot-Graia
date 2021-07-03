# ABot for Graia

这是一个从头屎到尾的 Bot

## ABot 现在能干什么

> - 阿里云文字转语音 `/tts <model> <msg>`
> - 兽语转换 `嗷 <msg>` and `呜 <msg>`
> - 小鸡词典查梗 `查梗 <msg>`
> - 小鸡词典文字转 emoji `emoji <msg>`
> - 汉语词典查询 `词典 <msg>`
> - 网易云音乐点歌（语音形式） `搜歌 <msg>` and `唱歌 <msg>`
> - 网络黑话翻译（字母缩写，如 `awsl` 等） `你在说什么 <msg>`
> - 词云生成 `我的月内总结` and `我的年内总结` and `本群月内总结` and `本群年内总结`
> - 我的世界服务器 Motd Ping `/mcping <host:port>`
> - 摸头 gif 生成 `摸头<@xxx>` and `[戳一戳]某人`
> - ~~涩图~~
> - Pornhub 风格的 logo 生成 `ph <msg> <msg>`
> - 亿些杂七杂八没整理的小功能
>   > - @bot 后的反馈 `@ABot`
>   > - 禁言群员 `/mute <@xxx>` and `/unmute <@xxx>`
>   > - 私聊接触群禁言（如果 ABot 是管理员但你不是且你被禁言的情况下）`/unmute <group> <qq>`
>   > - 禁言套餐（如果 ABot 是管理员的情况下）`我要禁言套餐`
>   > - 设置群员昵称（如果 ABot 是管理员的情况下）`/setnick <@xxx> <msg>`
>   > - 草 `草`
>   > - ABot 入群提醒
>   > - ABot 被踢出提醒
>   > - ABot 被修改权限提醒
>   > - ABot 被禁言提醒
>   > - ABot 私聊消息转发
>   > - 撤回群消息 `[回复]1`
>   > - 大清扫（如果 ABot 是管理员的情况下）`/viveall` and `/kickall`
>   > - 群名片修正
> - （待开发中）

## 部署 ABot

### 环境要求

- [Python](https://www.python.org/) `3.8`
- - [Poetry](https://python-poetry.org/)
- [Mirai HTTP API](https://github.com/project-mirai/mirai-api-http) `=< 1.12.0`

### 安装

1. 克隆 ABot 到本地
   ```shell
   git clone git@github.com:djkcyl/ABot-Graia.git
   ```
2. 安装依赖
   ```shell
   poetry install
   ```
3. 进入虚拟容器`每次运行前都需要进行`
   ```shell
   poerty shell
   ```
4. 修改 ABot 配置文件`config.py`

   ```python
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
   ```

5. 启动 ABot
   ```shell
   python main.py
   ```

**尽情享用吧~**

## 保持在后台运行

### **Windows**

> ~~Windows 系统也需要问吗？~~

### **Linux**
> **Centos**
> ```shell
> yum install screen
> screen -R ABot
> ...
> ```
> [Screen 基础用法](https://www.runoob.com/linux/linux-comm-screen.html)




~~代码太烂了，呜呜呜别骂了别骂了~~
