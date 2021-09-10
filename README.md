# ABot for Graia
### 由于不可抗力 ABot 暂时停更（
![7L4P%)_QA6_B3QPS0$74@49](https://user-images.githubusercontent.com/59153990/131785951-2d093dac-6d72-489b-a05d-0cbeab710c04.jpg)

![DT% IQ$B@{AGT_9J`}VIPQ3](https://user-images.githubusercontent.com/59153990/131631980-74f08a13-e638-4e7f-a42a-bceb33d75b3b.jpg)

## ABot 现在能干什么

> - 菜单以及功能介绍 `菜单` and `功能 <id>`
> - 群名片修正 `[被他人修改后自动触发]` and 私聊`群名片修正`
> - 微软文字转语音 `/tts <model> <msg>`
> - 兽语转换 `嗷 <msg>` and `呜 <msg>`
> - 小鸡词典查梗 `查梗 <msg>`
> - 小鸡词典文字转 emoji `emoji <msg>`
> - 汉语词典查询 `词典 <msg>`
> - 点歌姬（支持 \[QQ音乐 / 网易云音乐\] 以语音形式发送歌曲） `搜歌 <msg>` and `唱歌 <msg>`
> - 网络黑话翻译（字母缩写，如 `awsl` 等） `你在说什么 <msg>`
> - 词云生成 `查看个人词云` and `查看本群词云`
> - 我的世界服务器 Motd Ping `/mcping <host:port>`
> - 摸头 gif 生成 `摸头<@xxx>` and `[戳一戳]某人`
> - 涩图
> - 风格 logo 生成 `ph <msg> <msg>` and `5000兆 <msg> <msg>` and `yt <msg> <msg>`
> - 复读姬
> - 有点涩的词库？（
> - 废物证申请 `废物证申请`
> - 禁言套餐（如果 ABot 是管理员的情况下）`我要禁言套餐`
> - 防撤回（支持内容审核，检测是否为违禁内容）
> - 色图（随机生成色图 gif）
> - 娱乐功能
>   - 简单的经济系统
>     - 增加游戏币 私聊`充值 <qq> <数量>`
>     - 所有人增加游戏币 私聊`全员充值 <数量>`
>     - 赠送游戏币 `赠送游戏币 <@xxx> <数量>`
>   - 签到
>     - 查询当日签到率 私聊`签到率查询`
>   - **你画我猜**
>   - **奖券** `购买奖券` and `开奖查询`
>   - 排行榜（可查看游戏币榜和发言榜）`查看排行榜`
>   - （待开发中）
> - 简易骰娘 `.rdk` 可设置数量、面数、取最大前 n 个
> - 简单的作息系统（每日 0 点至 7 点半将自动关闭大部分功能）`休息` and `工作`
> - B 站视频解析
> - **听歌识曲**（识别语音形式的原曲或哼唱歌曲）`识曲 <原曲|哼唱>`
> - 白名单系统（将拒绝退出白名单外的群）私信`添加白名单 <group>` `取消白名单 <group>`
> - 淫文翻译机 `淫文`
> - **背单词**
> - 全局黑名单控制
> - 亿些杂七杂八没整理的小功能
>   - @bot 后的反馈 `@ABot`
>   - 私聊接触群禁言（如果 ABot 是管理员但你不是且你被禁言的情况下）`/unmute <group> <qq>`
>   - 设置群员昵称（如果 ABot 是管理员的情况下）`/setnick <@xxx> <msg>`
>   - 草 `草`
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

- [Python](https://www.python.org/) `3.8`
- - [Poetry](https://python-poetry.org/)
- [Mirai HTTP API](https://github.com/project-mirai/mirai-api-http) `1.12.0`
- [Redis](https://redis.io/)
- [Netease Cloud Music Api](https://github.com/Binaryify/NeteaseCloudMusicApi) `如果你需要点歌姬功能的话需要自行搭建`
- [QQ Music API](https://github.com/Rain120/qq-music-api) `如果你需要点歌姬功能的话需要自行搭建`

### 安装

1. 克隆 ABot 到本地
   ```shell
   git clone https://github.com/djkcyl/ABot-Graia
   ```
2. 更换虚拟容器的 Python 版本为 3.8
   ```shell
   poetry env use python3.8
   ```
3. 使用虚拟容器安装依赖
   ```shell
   poetry install
   ```
4. 进入虚拟容器`每次运行前都需要进行`
   ```shell
   poetry shell
   ```
5. 修改 ABot 配置文件 `config.exp.yaml` 后**并重命名**为 `config.yaml`
6. 启动 ABot
   ```shell
   python main.py
   ```

如果你的系统为 Ubuntu 你可能还需要执行下面这条命令才能正常使用词典功能

```shell
npx playwright install-deps
```

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
> > [Screen 基础用法](https://www.runoob.com/linux/linux-comm-screen.html)

~~代码太烂了，呜呜呜别骂了别骂了~~

感谢[SAGIRI-kawaii](https://github.com/SAGIRI-kawaii)的一堆功能
