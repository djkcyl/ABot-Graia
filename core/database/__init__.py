from loguru import logger
from typing import Optional
from pymongo import DESCENDING
from beanie import init_beanie, Document
from pymongo.errors import DuplicateKeyError
from motor.motor_asyncio import AsyncIOMotorClient

from .model import ABotMemberData, ABotEventData, ABotGroupData, ABotMessageData

mongodb_client: Optional[AsyncIOMotorClient] = None


async def init_database() -> AsyncIOMotorClient:
    global mongodb_client
    mongodb_client = AsyncIOMotorClient("mongodb://localhost:27017")
    await init_beanie(
        database=mongodb_client.ABot,
        document_models=[ABotMemberData, ABotGroupData, ABotEventData, ABotMessageData],
    )
    logger.info("数据库连接成功")
    return mongodb_client


async def get_mongodb_client() -> AsyncIOMotorClient:
    return mongodb_client or await init_database()


# uid 自增
async def get_next_uid(collection: Document) -> int:
    try:
        id = (
            await collection.find_all(
                limit=1,
                sort=("uid", DESCENDING),
            ).to_list()
        )[0].uid + 1
    except IndexError:
        id = 1

    return id


# 用户初始化
async def init_user(qq: int) -> Optional[ABotMemberData]:
    a = ABotMemberData(uid=await get_next_uid(ABotMemberData), qid=qq)
    ABotMemberData
    try:
        user: ABotMemberData = await a.insert()
        logger.info(f"已初始化{qq}，{user.uid}")
        return user
    except DuplicateKeyError:
        pass


# 获取用户信息
async def get_user(qq: int) -> Optional[ABotMemberData]:
    return await ABotMemberData.find_one(ABotMemberData.qid == qq)


# 群初始化
async def init_group(gid: int) -> Optional[ABotGroupData]:
    a = ABotGroupData(uid=await get_next_uid(ABotGroupData), gid=gid)
    try:
        group: ABotMemberData = await a.insert()
        logger.info(f"已初始化{gid}，{group.uid}")
        return group
    except DuplicateKeyError:
        pass


# 获取群信息
async def get_group(gid: int) -> Optional[ABotGroupData]:
    return await ABotGroupData.find_one(ABotGroupData.gid == gid)
