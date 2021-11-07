
```
ABot  根目录
├── FILE.md
├── README.md
├── config.exp.yaml  配置文件示例
├── config.py  配置管理
├── database  用户数据管理
│   ├── db.py
│   ├── talkData.db  聊天记录
│   ├── userData.db  用户数据
│   └── usertalk.py
├── font  字体
│   ├── FZDBSJW.TTF  方正大标宋
│   ├── sarasa-mono-sc-bold.ttf  更纱**
│   ├── sarasa-mono-sc-extralight.ttf
│   ├── sarasa-mono-sc-light.ttf
│   ├── sarasa-mono-sc-regular.ttf
│   ├── sarasa-mono-sc-semibold.ttf
│   └── vanfont.ttf  哔哩哔哩符号
├── groupdata.yaml  群配置
├── grouplist.yaml  群黑白名单
├── main.py  Bot 总入口
├── poetry.lock
├── pyproject.toml
├── userlist.json  用户黑名单
├── saya  插件目录
│   ├── AdminConfig.py  用于进行一些配置的操作
│   ├── AdminMSG.py  机器人管理员可用的指令
│   ├── AliTTS  阿里云文字转语音（已废弃）
│   ├── AnitRecall.py  防撤回
│   ├── AzureTTS  微软文字转语音
│   ├── Beast  兽语转换
│   ├── BilibiliDynamic  哔哩哔哩动态监控
│   ├── BilibiliResolve  哔哩哔哩视频解析
│   ├── BotEvent.py  bot事件处理
│   ├── ChatMS.py  色情词库
│   ├── ChickDict.py  小鸡词典查梗
│   ├── ChickEmoji.py  小鸡词典emoji转换
│   ├── ChineseDict  汉语词典
│   ├── CloudMusic  QQ音乐 | 网易云音乐 点歌姬
│   ├── CyberBlacktalk.py  能不能好好说话.jpg
│   ├── DailyAttendance.py  每日签到
│   ├── DailyNewspaper.py  日报
│   ├── DiceMaid.py  小骰娘
│   ├── DrawSomething  你画我猜
│   ├── Economy.py  经济系统（目前只有转账）
│   ├── EnglishTest  背英文单词
│   │   └── database
│   │       └── WordData.db  单词词库
│   ├── Lottery  彩票（建议别玩，容易封号）
│   ├── Message  有的没的消息回复
│   ├── MinecraftPing  我的世界服务器Motd Ping
│   │   └── statusping.py  服务器 ping 包解析
│   ├── MutePack.py  禁言套餐
│   ├── PetPet  摸头
│   ├── Pixiv.py  p站涩图
│   ├── Repeater.py  复读姬
│   ├── Setu  通过pillow生成的随机“色图”
│   ├── StyleLogoGenerator  风格logo生成
│   ├── SystemStatus.py  系统占用监控
│   ├── TalkStatistics  消息量分析
│   ├── TrashCard.py  废物证生成
│   ├── UserFunc.py  用户功能（目前只有排行榜）
│   ├── VoiceMusicRecognition.py  听歌识曲
│   ├── WordCloud  词云
│   └── Yinglish.py  淫文翻译姬
└── util  通用功能
    ├── cut_string.py  文字切割（自动换行）
    ├── ImageModeration.py  图片安全审核
    ├── QRGeneration.py  二维码生成
    ├── RestControl.py  作息控制
    ├── TextModeration.py  文字安全审核
    ├── UserBlock.py  用户黑名单
    ├── aiorequests.py  异步http（已废弃）
    ├── browser  无头浏览器
    ├── limit.py  消息频率控制
    ├── md2image  Markdown转图片
    └── text2image.py  文字转图片
```