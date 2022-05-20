import time

from graia.ariadne.model import Member, Group
from ..database.model import ABotMemberData, ABotGroupData
from graia.broadcast.entities.dispatcher import BaseDispatcher
from graia.broadcast.interfaces.dispatcher import DispatcherInterface
from ..database import init_user, get_user, init_group, get_group


class ABotMember(Member):
    def __init__(self, member: Member):
        super().__init__(**member.dict())

    async def get_data(self) -> ABotMemberData:
        return await get_user(self.id) or await init_user(self.id)

    async def ban(
        self, operator: int = 0, duration: int = 0, group: int = 0, reason: str = ""
    ) -> None:
        data = await self.get_data()
        data.ban.status = True
        data.ban.operator = operator
        data.ban.unban_time = int(time.time() + duration) if duration else 0
        data.ban.group = group
        data.ban.reason = reason
        await data.save()

    async def unban(self) -> None:
        data = await self.get_data()
        data.ban.status = False
        data.ban.operator = None
        data.ban.unban_time = None
        data.ban.group = None
        data.ban.reason = None
        await data.save()

    async def get_banned(self) -> bool:
        data = await self.get_data()
        return data.ban.status

    async def add_gold(self, num: int) -> int:
        data = await self.get_data()
        data.coin.total_num += num
        await data.save()
        return data.coin.total_num

    async def reduce_coin(self, num: int, forec: bool = False, all: bool = False) -> int:
        data = await self.get_data()
        if not all and data.coin.total_num >= num and forec:
            data.coin.total_num -= num
            await data.save()
            return num
        elif not all and data.coin.total_num >= num:
            return 0
        else:
            reduce_num = data.coin.total_num
            data.coin.total_num = 0
            await data.save()
            return reduce_num

    async def add_answer(self, answer: str) -> None:
        data = await self.get_data()
        if answer == "english":
            data.answers.english += 1
        elif answer == "arknights":
            data.answers.arknights += 1
        await data.save()

    async def get_coin(self) -> int:
        data = await self.get_data()
        return data.coin.total_num

    async def sign(self) -> bool:
        data = await self.get_data()
        if data.sign.is_sign:
            return False
        data.sign.is_sign = True
        data.sign.total_days += 1
        data.sign.continuous_days += 1
        await data.save()
        return True

    async def add_talk(self, event_id: int) -> None:
        data = await self.get_data()
        data.talk.total_num += 1
        data.talk.last_talk.event = event_id
        await data.save()


class ABotGroup(Group):
    def __init__(self, group: Group):
        super().__init__(**group.dict())

    async def get_data(self) -> ABotGroupData:
        return await get_group(self.id) or await init_group(self.id)

    async def set_whitelist(self, operator: int = 0) -> None:
        data = await self.get_data()
        data.wblist.whitelist.status = True
        data.wblist.whitelist.operator = operator
        await data.save()

    async def set_blacklist(self, operator: int = 0, reason: str = "") -> None:
        data = await self.get_data()
        data.wblist.blacklist.status = True
        data.wblist.blacklist.operator = operator
        data.wblist.blacklist.reason = reason
        await data.save()

    async def remove_whitelist(self) -> None:
        data = await self.get_data()
        data.wblist.whitelist.status = False
        data.wblist.whitelist.operator = None
        await data.save()

    async def remove_blacklist(self) -> None:
        data = await self.get_data()
        data.wblist.blacklist.status = False
        data.wblist.blacklist.operator = None
        data.wblist.blacklist.reason = None
        await data.save()

    async def set_function(self, func: str, status: bool) -> bool:
        data = await self.get_data()
        data.functions.disabled.remove(
            func
        ) if status else data.functions.disabled.append(func)

    async def get_function(self, func: str) -> bool:
        data = await self.get_data()
        return func not in data.functions.disabled


class ABotMemberDispatcher(BaseDispatcher):
    async def catch(self, interface: DispatcherInterface):
        if interface.annotation == ABotMember:
            member: Member = await interface.lookup_param("member", Member, None)
            return ABotMember(member)


class ABotGroupDispatcher(BaseDispatcher):
    async def catch(self, interface: DispatcherInterface):
        if interface.annotation == ABotGroup:
            group: Group = await interface.lookup_param("group", Group, None)
            return ABotGroup(group)
