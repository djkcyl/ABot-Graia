import httpx
import asyncio

from saucenao_api import AIOSauceNao
from graia.saya import Saya, Channel
from graia.application.group import Group, Member
from graia.broadcast.interrupt.waiter import Waiter
from graia.application import GraiaMiraiApplication
from graia.broadcast.interrupt import InterruptControl
from graia.application.event.messages import GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.parser.literature import Literature
from graia.application.message.elements.internal import At, MessageChain, Plain, Image_UnsafeBytes, Image, Source

from datebase.db import reduce_gold
from config import yaml_data, group_data
from util.limit import member_limit_check
from util.UserBlock import group_black_list_block

from .draw import draw_tracemoe

saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
inc = InterruptControl(bcc)
query = '''
query ($ids: [Int]) {
    Page(page: 1, perPage: 50) {
        media(id_in: $ids, type: ANIME) {
        id
        title {
            native
            romaji
            english
        }
        type
        format
        status
        startDate {
            year
            month
            day
        }
        endDate {
            year
            month
            day
        }
        season
        episodes
        duration
        coverImage {
            large
        }
        genres
        synonyms
        isAdult
        }
    }
}
'''

V_RUNING = False
I_RUNING = False
WAITING = []


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Literature("以图搜番")],
                            headless_decorators=[member_limit_check(30), group_black_list_block()]))
async def anime_search(app: GraiaMiraiApplication, group: Group, member: Member, message: MessageChain, source: Source):

    if yaml_data['Saya']['AnimeSceneSearch']['Disabled']:
        return
    elif 'AnimeSceneSearch' in group_data[group.id]['DisabledFunc']:
        return

    @Waiter.create_using_function([GroupMessage])
    async def waiter1(waiter1_group: Group, waiter1_member: Member, waiter1_message: MessageChain):
        if all([waiter1_group.id == group.id, waiter1_member.id == member.id]):
            waiter1_saying = waiter1_message.asDisplay()
            if waiter1_saying == "取消":
                return False
            elif waiter1_message.has(Image):
                return waiter1_message.getFirst(Image).url
            else:
                await app.sendGroupMessage(group, MessageChain.create([Plain("请发送图片")]))

    global V_RUNING

    if V_RUNING:
        await app.sendGroupMessage(group, MessageChain.create([Plain("以图搜番正在运行，请稍后再试")]))
    else:
        if message.has(Image):
            image_url = message.getFirst(Image).url
        else:
            WAITING.append(member.id)
            waite = await app.sendGroupMessage(group, MessageChain.create([Plain(f"请发送图片以继续，发送取消可终止搜番")]))
            try:
                image_url = await asyncio.wait_for(inc.wait(waiter1), timeout=20)
                if not image_url:
                    WAITING.remove(member.id)
                    return await app.sendGroupMessage(group, MessageChain.create([Plain("已取消")]))
            except asyncio.TimeoutError:
                WAITING.remove(member.id)
                return await app.sendGroupMessage(group, MessageChain.create([
                    Plain("等待超时")
                ]), quote=waite.messageId)

        if await reduce_gold(str(member.id), 4):
            V_RUNING = True
            await app.sendGroupMessage(group, MessageChain.create([Plain("正在搜索，请稍后")]), quote=source)

            async with httpx.AsyncClient(timeout=45) as client:

                params = {
                    "key": yaml_data['Saya']['AnimeSceneSearch']['tracemoe_key'],
                    "url": image_url
                }
                r = await client.get("https://api.trace.moe/search", params=params)
                search_res = r.json()
                if "result" not in search_res:
                    V_RUNING = False
                    return await app.sendGroupMessage(group, MessageChain.create([
                        Plain("搜索失败")
                    ]))
                data = {
                    "query": query,
                    "variables": {
                        "ids": [search_res["result"][0]["anilist"]]
                    }
                }
                r = await client.post("https://trace.moe/anilist/", json=data)
                media_res = r.json()
                print(media_res)

            image = await draw_tracemoe(search_res["result"][0], media_res["data"]["Page"]["media"][0])
            await app.sendGroupMessage(group, MessageChain.create([Image_UnsafeBytes(image)]), quote=source)

            V_RUNING = False
        else:
            await app.sendGroupMessage(group, MessageChain.create([
                At(member.id),
                Plain(" 你的游戏币不足，无法使用")
            ]))


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Literature("以图搜图")],
                            headless_decorators=[member_limit_check(30), group_black_list_block()]))
async def anime_search_pic(app: GraiaMiraiApplication, group: Group, member: Member, message: MessageChain, source: Source):
    if yaml_data['Saya']['AnimeSceneSearch']['Disabled']:
        return
    elif 'AnimeSceneSearch' in group_data[group.id]['DisabledFunc']:
        return

    @Waiter.create_using_function([GroupMessage])
    async def waiter1(waiter1_group: Group, waiter1_member: Member, waiter1_message: MessageChain):
        if all([waiter1_group.id == group.id, waiter1_member.id == member.id]):
            waiter1_saying = waiter1_message.asDisplay()
            if waiter1_saying == "取消":
                return False
            elif waiter1_message.has(Image):
                return waiter1_message.getFirst(Image).url
            else:
                await app.sendGroupMessage(group, MessageChain.create([Plain("请发送图片")]))

    global I_RUNING

    if I_RUNING:
        await app.sendGroupMessage(group, MessageChain.create([Plain("以图搜图正在运行，请稍后再试")]))
    else:
        if message.has(Image):
            image_url = message.getFirst(Image).url
        else:
            WAITING.append(member.id)
            waite = await app.sendGroupMessage(group, MessageChain.create([Plain(f"请发送图片以继续，发送取消可终止搜图")]))
            try:
                image_url = await asyncio.wait_for(inc.wait(waiter1), timeout=20)
                if not image_url:
                    WAITING.remove(member.id)
                    return await app.sendGroupMessage(group, MessageChain.create([Plain("已取消")]))
            except asyncio.TimeoutError:
                WAITING.remove(member.id)
                return await app.sendGroupMessage(group, MessageChain.create([
                    Plain("等待超时")
                ]), quote=waite.messageId)
        if await reduce_gold(str(member.id), 4):
            I_RUNING = True
            await app.sendGroupMessage(group, MessageChain.create([Plain("正在搜索，请稍后")]), quote=source)
            async with AIOSauceNao(yaml_data['Saya']['AnimeSceneSearch']['saucenao_key'], numres=3) as snao:
                try:
                    results = await snao.from_url(image_url)
                except:
                    I_RUNING = False
                    return await app.sendGroupMessage(group, MessageChain.create([
                        Plain("搜索失败")
                    ]))
            results_list = []
            for results in results.results:
                print(results.urls)
                url_list = []
                for url in results.urls:
                    url_list.append(url)
                if len(url_list) == 0:
                    continue
                urls = '\n'.join(url_list)
                results_list.append(f"相似度：{results.similarity}%\n标题：{results.title}\n节点名：{results.index_name}\n链接：{urls}")

            if len(results_list) == 0:
                await app.sendGroupMessage(group, MessageChain.create([
                    Plain("未找到有价值的数据")
                ]), quote=source)
                I_RUNING = False
            else:
                await app.sendGroupMessage(group, MessageChain.create([
                    Plain("\n==================\n".join(results_list))
                ]), quote=source)
                I_RUNING = False
        else:
            await app.sendGroupMessage(group, MessageChain.create([
                At(member.id),
                Plain(" 你的游戏币不足，无法使用")
            ]))
