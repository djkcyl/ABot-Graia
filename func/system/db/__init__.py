from loguru import logger
from graia.saya import Channel
from beanie import init_beanie, Document
from motor.motor_asyncio import AsyncIOMotorClient
from graia.ariadne.event.lifecycle import ApplicationLaunched
from graia.saya.builtins.broadcast.schema import ListenerSchema

from core.model import FuncType
from core.function import build_metadata

channel = Channel.current()
channel.meta = build_metadata(
    func_type=FuncType.system,
    name="数据库",
    version="1.0",
    description="数据库初始化",
    can_be_disabled=False,
    hidden=True,
)


@channel.use(ListenerSchema(listening_events=[ApplicationLaunched], priority=1))
async def main():
    database_uri = "mongodb://localhost:27017"
    client = AsyncIOMotorClient(database_uri)["abot"]
    document_models = Document.__subclasses__()
    await init_beanie(
        database=client,
        document_models=document_models,  # type: ignore
    )

    for model in document_models:
        logger.info(f"[Task.db] 数据库模型 {model.__name__} 初始化完成")
    logger.success("[Task.db] 数据库初始化完成")
