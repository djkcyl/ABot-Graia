# ABot for Graia

这是一个从头屎到尾的 Bot

## ABot 现在能干什么

> - 阿里云文字转语音 `/tts <model> <msg>`
> - 兽语转换 `嗷 <msg>` and `呜 <msg>`
> - 小鸡词典查梗 `查梗 <msg>`
> - 小鸡词典文字转 emoji `emoji <msg>`
> - 汉语词典查询 `词典 <msg>`
> - 网易云音乐点歌姬（语音形式） `搜歌 <msg>` and `唱歌 <msg>`
> - 网络黑话翻译（字母缩写，如 `awsl` 等） `你在说什么 <msg>`
> - 词云生成 `我的月内总结` and `我的年内总结` and `本群月内总结` and `本群年内总结`
> - 我的世界服务器 Motd Ping `/mcping <host:port>`
> - 摸头 gif 生成 `摸头<@xxx>` and `[戳一戳]某人`
> - 涩图
> - Pornhub 风格的 logo 生成 `ph <msg> <msg>`
> - 复读姬
> - 有点涩的词库？（
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

群管理或 bot admin 输入 `管理员菜单` 即可打开管理员控制

## 部署 ABot

### 环境要求

- [Python](https://www.python.org/) `3.8`
- - [Poetry](https://python-poetry.org/)
- [Mirai HTTP API](https://github.com/project-mirai/mirai-api-http) `=< 1.12.0`
- [Netease Cloud Music Api](https://github.com/Binaryify/NeteaseCloudMusicApi) `如果你需要网易云音乐点歌姬功能的话需要自行搭建`

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
   poetry shell
   ```
4. 修改 ABot 配置文件 `config.exp.yaml` 后**并重命名**为 `config.exp.yaml`
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
> > ```shell
> > yum install screen
> > screen -R ABot
> > ...
> > ```
> 其他发行版怎么用就不多说了，自己查吧
> [Screen 基础用法](https://www.runoob.com/linux/linux-comm-screen.html)


ABot 的 saya 插件应该都可以抠出来放在别的 graia bot 里使用

~~代码太烂了，呜呜呜别骂了别骂了~~

