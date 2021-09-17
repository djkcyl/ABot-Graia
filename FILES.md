
```
ABot  根目录
├── FILE.md
├── README.md
├── config.exp.yaml  配置文件示例
├── config.py  配置管理
├── datebase  用户数据管理
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
├── main.py  
├── poetry.lock
├── pyproject.toml
├── userlist.json  用户黑名单
├── saya  插件目录
│   ├── AdminConfig.py  用于进行一些配置的操作
│   ├── AdminMSG.py  机器人管理员可用的指令
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
```