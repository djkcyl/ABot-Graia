<div align="center">

# ABot for Graia

</div>

### 由于不可抗力 ABot 暂时停更（

![7L4P%)_QA6_B3QPS0$74@49](https://user-images.githubusercontent.com/59153990/131785951-2d093dac-6d72-489b-a05d-0cbeab710c04.jpg)

![DT% IQ$B@{AGT_9J`}VIPQ3](https://user-images.githubusercontent.com/59153990/131631980-74f08a13-e638-4e7f-a42a-bceb33d75b3b.jpg)

## ABot 现在能干什么

> - 菜单以及功能介绍
> - 群名片修正 ~~`[被他人修改后自动触发]`~~ and 私聊`群名片修正`
> - 微软文字转语音
> - 兽语转换
> - 小鸡词典查梗
> - 小鸡词典文字转 emoji
> - 汉语词典查询
> - 点歌姬（支持 \[QQ 音乐 / 网易云音乐\] 以语音形式发送歌曲）
> - 网络黑话翻译（字母缩写，如 `awsl` 等）
> - 词云生成
> - 我的世界服务器 Motd Ping
> - 摸头 gif 生成
> - 涩图
> - 风格 logo 生成
> - 复读姬
> - 有点涩的词库？（
> - 废物证申请 `废物证申请`
> - 禁言套餐（如果 ABot 是管理员的情况下）
> - 防撤回（支持内容审核，检测是否为违禁内容）
> - 色图（随机生成色图 gif）
> - 娱乐功能
>   - 简单的经济系统
>     - 增加游戏币 私聊`充值 <qq> <数量>`
>     - 所有人增加游戏币 私聊`全员充值 <数量>`
>     - 赠送游戏币
>   - 签到
>     - 查询当日签到率 私聊`签到率查询`
>   - **你画我猜**
>   - **奖券**
>   - 排行榜（可查看游戏币榜和发言榜）`查看排行榜`
>   - （待开发中）
> - 简易骰娘（可设置数量、面数、取最大前 n 个）
> - 简单的作息系统（每日 0 点至 7 点半将自动关闭大部分功能）`休息` and `工作`
> - BiliBili 视频解析
> - **听歌识曲**（识别语音形式的原曲或哼唱歌曲）
> - 白名单系统（将拒绝退出白名单外的群）私信`添加白名单 <group>` `取消白名单 <group>`
> - 淫文翻译机
> - **背单词**
> - 全局黑名单控制
> - 消息量统计 `查看消息量统计`
> - **BiliBili 动态订阅推送**
> - 亿些杂七杂八没整理的小功能
>   - @bot 后的反馈
>   - 草
>   - ABot 入群提醒
>   - ABot 被踢出提醒
>   - ABot 被修改权限提醒
>   - ABot 被禁言提醒
>   - ABot 私聊消息转发
>   - 撤回群消息 `[回复]1`
>   - 大清扫（如果 ABot 是管理员的情况下）`/viveall` and `/kickall`
> - （待开发中）

## 部署 ABot

### 环境要求

- [Python](https://www.python.org/) `^3.8`
  - [Poetry](https://python-poetry.org/)
- [Mirai HTTP API](https://github.com/project-mirai/mirai-api-http) `1.12.0`
- [Redis](https://redis.io/)
- [Netease Cloud Music Api](https://github.com/Binaryify/NeteaseCloudMusicApi) `如果你需要点歌姬功能的话需要自行搭建`
- [QQ Music API](https://github.com/Rain120/qq-music-api) `如果你需要点歌姬功能的话需要自行搭建`

### 安装

1. 克隆 ABot 到本地
   ```shell
   git clone https://github.com/djkcyl/ABot-Graia
   ```
2. 使用虚拟容器安装依赖
   ```shell
   poetry install
   ```
3. 进入虚拟容器`每次运行前都需要进行`
   ```shell
   poetry shell
   ```
4. 修改 ABot 配置文件 `config.exp.yaml` 后**并重命名**为 `config.yaml`
5. 启动 ABot
   ```shell
   python main.py
   ```

> 你可能还需要执行下面这条命令才能正常使用词典功能
>
> ```shell
> npx playwright install-deps
> ```

**尽情享用吧~**

## 保持在后台运行

### **Windows**

> ~~Windows 系统也需要问吗？~~

### **Linux**

> **Centos**
>
> ```shell
> yum install screen
> screen -R ABot
> ...
> ```
>
> 其他发行版怎么用就不多说了，自己查吧
> [Screen 基础用法](https://www.runoob.com/linux/linux-comm-screen.html)

<details><summary>## 目录结构</summary>
ABot
├── FILE.md
├── README.md
├── config.exp.yaml
├── config.py
├── datebase
│   ├── db.py
│   ├── talkData.db
│   ├── userData.db
│   └── usertalk.py
├── font
│   ├── FZDBSJW.TTF
│   ├── sarasa-mono-sc-bold.ttf
│   ├── sarasa-mono-sc-extralight.ttf
│   ├── sarasa-mono-sc-light.ttf
│   ├── sarasa-mono-sc-regular.ttf
│   ├── sarasa-mono-sc-semibold.ttf
│   └── vanfont.ttf
├── groupdata.yaml
├── grouplist.yaml
├── main.py
├── poetry.lock
├── pyproject.toml
├── userlist.json
├── saya
│   ├── 2048
│   │   ├── 2048.py
│   │   ├── __init__.py
│   ├── AdminConfig.py
│   ├── AdminMSG.py
│   ├── AliTTS
│   │   ├── __init__.py
│   │   ├── get_token.py
│   │   └── post_tts_text.py
│   ├── AnitRecall.py
│   ├── Ark
│   │   ├── __init__.py
│   │   └── dbop.py
│   ├── ArkFriend
│   │   ├── ArkTagGetter.py
│   │   ├── FavorData.py
│   │   ├── __init__.py
│   │   ├── ark_operate.py
│   │   └── database
│   │       └── database.py
│   ├── ArkrecWIKI
│   │   ├── __init__.py
│   ├── AzureTTS
│   │   ├── __init__.py
│   ├── Beast
│   │   ├── __init__.py
│   │   └── beast.py
│   ├── BilibiliDynamic
│   │   ├── __init__.py
│   │   ├── dynamic_list.json
│   │   └── dynamic_shot.py
│   ├── BilibiliResolve
│   │   ├── __init__.py
│   │   └── draw_bili_image.py
│   ├── BotEvent.py
│   ├── ChaoxingSign
│   │   ├── __init__.py
│   │   └── data.json
│   ├── ChatMS.py
│   ├── ChickDict.py
│   ├── ChickEmoji.py
│   ├── ChineseDict
│   │   ├── __init__.py
│   │   ├── page_screenshot.py
│   ├── CloudMusic
│   │   ├── __init__.py
│   ├── CyberBlacktalk.py
│   ├── DailyAttendance.py
│   ├── DailyNewspaper.py
│   ├── DiceMaid.py
│   ├── DrawSomething
│   │   ├── __init__.py
│   │   ├── qr.jpg
│   │   └── word.json
│   ├── Economy.py
│   ├── EnglishTest
│   │   ├── __init__.py
│   │   ├── database
│   │   │   ├── WordData.db
│   │   │   └── database.py
│   │   ├── update.py
│   │   └── worddict
│   │       └── *
│   ├── Lottery
│   │   ├── __init__.py
│   │   ├── certification.py
│   │   ├── data.json
│   │   ├── lottery_image.py
│   │   ├── msyhbd.ttc
│   │   ├── server-private.pem
│   │   └── server-public.pem
│   ├── Message
│   │   ├── __init__.py
│   │   ├── haoye.png
│   │   ├── huangdou.jpg
│   │   └── setu_qr.png
│   ├── MinecraftPing
│   │   ├── __init__.py
│   │   ├── mcping.py
│   │   └── statusping.py
│   ├── MutePack.py
│   ├── PetPet
│   │   ├── PetPetFrames
│   │   │   ├── frame0.png
│   │   │   ├── frame1.png
│   │   │   ├── frame2.png
│   │   │   ├── frame3.png
│   │   │   ├── frame4.png
│   │   ├── __init__.py
│   ├── Pixiv.py
│   ├── Repeater.py
│   ├── Setu
│   │   ├── __init__.py
│   │   └── setu.py
│   ├── StyleLogoGenerator
│   │   ├── __init__.py
│   │   └── ttf
│   │       ├── ArialEnUnicodeBold.ttf
│   │       └── STKAITI.TTF
│   ├── SystemStatus.py
│   ├── TalkStatistics
│   │   ├── __init__.py
│   │   └── mapping.py
│   ├── TrashCard.py
│   ├── UserFunc.py
│   ├── VoiceMusicRecognition.py
│   ├── WordCloud
│   │   ├── __init__.py
│   │   └── bgg.jpg
│   ├── Yinglish.py
│   └── test.py
├── util
│   ├── CutString.py
│   ├── ImageModeration.py
│   ├── QRGeneration.py
│   ├── RestControl.py
│   ├── TextModeration.py
│   ├── UpImage.py
│   ├── UserBlock.py
│   ├── aiorequests.py
│   ├── browser
│   │   ├── __init__.py
│   │   ├── data
│   │   └── extension
│   │       └── ad
│   ├── limit.py
│   ├── md2image
│   │   ├── default.css
│   │   └── test.py
│   └── text2image.py
</details>

> 如果有什么需要的，可以发issue或者加我的QQ：`2948531755`。

感谢[SAGIRI-kawaii](https://github.com/SAGIRI-kawaii)的一堆功能
