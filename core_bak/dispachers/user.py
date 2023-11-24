from loguru import logger
from graia.broadcast.entities.dispatcher import BaseDispatcher
from graia.broadcast.interfaces.dispatcher import DispatcherInterface
from graia.ariadne.event.message import GroupMessage

from ..db_model import AUser, GroupData
from ..model import AUserModel, AGroupModel


class ABotDispatcher(BaseDispatcher):
    @staticmethod
    async def catch(interface: DispatcherInterface[GroupMessage]):
        if interface.annotation == AUserModel:
            qid = str(interface.event.sender.id)
            if not await AUser.find_one(AUser.qid == qid):
                last_userid = await AUser.find_one(sort=[("_id", -1)])
                user_id = int(last_userid.uid) + 1 if last_userid else 1
                await AUser(uid=user_id, qid=qid).insert()  # type: ignore
                logger.info(f"[Core.db] 已初始化用户：{qid}")
            user = await AUser.find_one(AUser.qid == qid)
            assert user
            return await AUserModel.init(user)
        if interface.annotation == AGroupModel:
            group_id = str(interface.event.sender.group.id)
            if not await GroupData.find_one(GroupData.group_id == group_id):
                await GroupData(group_id=group_id).insert()  # type: ignore
                logger.info(f"[Core.db] 已初始化群：{group_id}")
            group = await GroupData.find_one(GroupData.group_id == group_id)
            assert group
            return await AGroupModel.init(group)
