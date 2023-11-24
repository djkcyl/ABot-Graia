import pkgutil
from asyncio import AbstractEventLoop
from pathlib import Path

import creart
import kayaku
from avilla.core.application import Avilla
from avilla.elizabeth.protocol import ElizabethConfig, ElizabethProtocol
from avilla.qqapi.protocol import Intents, QQAPIConfig, QQAPIProtocol
from graia.broadcast import Broadcast
from graia.saya import Saya
from launart import Launart

# ruff: noqa: E402
# import 需要 kayaku 的包前需要先初始化 kayaku
kayaku.initialize({"{**}": "./config/{**}"})

from utils.aiohttp_service import AiohttpClientService
from utils.config import BasicConfig

loop = creart.create(AbstractEventLoop)
bcc = creart.create(Broadcast)
saya = creart.create(Saya)
launart = creart.create(Launart)
avilla = Avilla(broadcast=bcc, launch_manager=launart, message_cache_size=0)

with saya.module_context():
    for module in pkgutil.iter_modules(["saya"]):
        saya.require(f"saya.{module.name}")

# Avilla 默认添加 MemcacheService
launart.add_component(AiohttpClientService())

# import 完各种包之后在启动 kayaku
kayaku.bootstrap()

config = kayaku.create(BasicConfig)

if config.protocol.miraiApiHttp.enabled:
    avilla.apply_protocols(
        ElizabethProtocol().configure(
            ElizabethConfig(
                config.protocol.miraiApiHttp.qq,
                config.protocol.miraiApiHttp.host,
                config.protocol.miraiApiHttp.port,
                config.protocol.miraiApiHttp.access_token,
            )
        )
    )

if config.protocol.QQAPI.enabled:
    avilla.apply_protocols(
        QQAPIProtocol().configure(
            QQAPIConfig(
                config.protocol.QQAPI.id,
                config.protocol.QQAPI.token,
                config.protocol.QQAPI.secret,
                config.protocol.QQAPI.shard,
                config.protocol.QQAPI.intent,
                config.protocol.QQAPI.is_sandbox,
            )
        )
    )

avilla.launch()

# 可选的：退出时保存所有配置
# （会导致运行时手动更改的配置文件会被还原）
kayaku.save_all()
