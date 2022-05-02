import asyncio

from graia.ariadne.model import Member, Group, MemberPerm
from core.model import ABotMember

from core.database import get_mongodb_client


async def main():
    await get_mongodb_client()
    member = Member(
        id=23333333,
        memberName="test",
        permission=MemberPerm.Member,
        group=Group(id=1, name="test", permission=MemberPerm.Member),
    )
    amember = ABotMember(member)
    await amember.ban(operator=1, duration=10, group=1, reason="test")
    print(await amember.get_data())


asyncio.run(main())
