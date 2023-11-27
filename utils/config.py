from dataclasses import dataclass, field

from avilla.qqapi.protocol import Intents
from kayaku import config


@dataclass
class ElizabethConfig:
    enabled: bool = False
    qq: int = 0
    """机器人QQ号"""
    host: str = "localhost"
    """mirai-api-http 监听地址"""
    port: int = 8080
    """mirai-api-http 监听端口"""
    access_token: str = "underfined"
    """mirai-api-http 的 verifyKey"""


@dataclass
class QQAPIConfig:
    enabled: bool = False
    id: str = "undefined"
    """AppID (机器人ID)"""
    token: str = "undefined"
    """Token (机器人令牌)"""
    secret: str = "undefined"
    """AppSecret (机器人密钥)"""
    shard: tuple[int, int] | None = None
    intent: Intents = field(default_factory=Intents)
    is_sandbox: bool = False
    """是否是沙箱环境"""


@dataclass
class Protocol:
    QQAPI: QQAPIConfig = field(default_factory=QQAPIConfig)
    miraiApiHttp: ElizabethConfig = field(default_factory=ElizabethConfig)


@config("main")
class BasicConfig:
    logChat: bool = True
    """是否将聊天信息打印在日志中"""
    debug: bool = False
    """是否启用调试模式"""
    protocol: Protocol = field(default_factory=Protocol)
    database_uri: str = "mongodb://localhost:27017"
    """MongoDB数据库uri"""
