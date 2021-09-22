## 部署 ABot

### 环境要求

- 为必须
  - 为可选

- [Python](https://www.python.org/) `^3.8`
  - [Poetry](https://python-poetry.org/)
- [Mirai HTTP API](https://github.com/project-mirai/mirai-api-http) `1.12.0`
- [Redis](https://redis.io/)
  - [Netease Cloud Music Api](https://github.com/Binaryify/NeteaseCloudMusicApi) `如果你需要点歌姬功能的话需要自行搭建`
  - [QQ Music API](https://github.com/Rain120/qq-music-api) `如果你需要点歌姬功能的话需要自行搭建`

### 安装

带星号的是安装了可选组件 `Poetry` 的步骤。

1. 克隆 ABot 到本地
   ```shell
   git clone https://github.com/djkcyl/ABot-Graia
   ```
2*. 使用虚拟容器安装依赖
   ```shell
   poetry install
   ```
3*. 进入虚拟容器<br>
注：**每次运行前都需要进行**
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

> ~~Windows 系统也需要问吗？彳亍~~
> 按下最小化即可。
> ~~为什么会有人这个也要教啊（恼）~~

### **Linux**

> **Centos**
>
> ```shell
> yum install screen
> screen -R ABot
> ...
> ```
>
> 其他发行版怎么用请查阅[此处](https://www.runoob.com/linux/linux-comm-screen.html)
