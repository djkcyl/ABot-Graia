import httpx
import asyncio

from saucenao_api import AIOSauceNao
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from saucenao_api.errors import SauceNaoApiError
from graia.broadcast.interrupt.waiter import Waiter
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.model import Friend, Group, Member
from graia.broadcast.interrupt import InterruptControl
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.literature import Literature
from graia.ariadne.message.element import At, Plain, Image, Source
from graia.ariadne.event.message import FriendMessage, GroupMessage

from database.db import reduce_gold
from config import yaml_data, group_data
from util.control import Permission, Interval

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
saucenao_usage = None


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Literature("以图搜番")],
                            decorators=[Permission.require(), Interval.require()]))
async def anime_search(app: Ariadne, group: Group, member: Member, message: MessageChain, source: Source):

    if yaml_data['Saya']['AnimeSceneSearch']['Disabled']:
        return
    elif 'AnimeSceneSearch' in group_data[str(group.id)]['DisabledFunc']:
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
            waite = await app.sendGroupMessage(group, MessageChain.create([Plain("请发送图片以继续，发送取消可终止搜番")]))
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
            await app.sendGroupMessage(group, MessageChain.create([
                Plain("正在搜索，请稍后\n仅可搜索日本番剧\n不支持有边框的截图，不支持裁切截图，不支持镜像截图，不支持滤色截图，不支持老动漫，不支持一切非动漫原画图\n详情请查看https://trace.moe/faq")
            ]), quote=source.id)

            async with httpx.AsyncClient(timeout=15) as client:

                params = {
                    "key": yaml_data['Saya']['AnimeSceneSearch']['tracemoe_key'],
                    "url": image_url
                }
                error = None
                for _ in range(3):
                    try:
                        r = await client.get("https://api.trace.moe/search", params=params)
                        if r.status_code == 402:
                            del params["key"]
                            continue
                        break
                    except httpx.ReadTimeout:
                        try:
                            del params["key"]
                        except KeyError:
                            pass
                    except httpx.HTTPError as e:
                        error = type(e)
                        asyncio.sleep(1)
                else:
                    V_RUNING = False
                    return await app.sendGroupMessage(group, MessageChain.create([
                        Plain(f"搜索失败 {error}")
                    ]))

                search_res = r.json()
                if "result" not in search_res:
                    V_RUNING = False
                    return await app.sendGroupMessage(group, MessageChain.create([
                        Plain(f"搜索失败 {search_res['error']}")
                    ]))
                data = {
                    "query": query,
                    "variables": {
                        "ids": [search_res["result"][0]["anilist"]]
                    }
                }
                r = await client.post("https://trace.moe/anilist/", json=data)
                media_res = r.json()

            image = await draw_tracemoe(search_res["result"][0], media_res["data"]["Page"]["media"][0])
            await app.sendGroupMessage(group, MessageChain.create([Image(data_bytes=image)]), quote=source.id)

            V_RUNING = False
        else:
            await app.sendGroupMessage(group, MessageChain.create([
                At(member.id),
                Plain(" 你的游戏币不足，无法使用")
            ]))


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Literature("以图搜图")],
                            decorators=[Permission.require(), Interval.require()]))
async def saucenao(app: Ariadne, group: Group, member: Member, message: MessageChain, source: Source):

    if yaml_data['Saya']['AnimeSceneSearch']['Disabled']:
        return
    elif 'AnimeSceneSearch' in group_data[str(group.id)]['DisabledFunc']:
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
            waite = await app.sendGroupMessage(group, MessageChain.create([Plain("请发送图片以继续，发送取消可终止搜图")]))
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
            await app.sendGroupMessage(group, MessageChain.create([Plain("正在搜索，请稍后")]), quote=source.id)
            async with AIOSauceNao(yaml_data['Saya']['AnimeSceneSearch']['saucenao_key'], numres=3) as snao:
                try:
                    results = await snao.from_url(image_url)
                except SauceNaoApiError as e:
                    I_RUNING = False
                    return await app.sendGroupMessage(group, MessageChain.create([
                        Plain(f"搜索失败 {type(e)} {e.__str__()}")
                    ]))
            global saucenao_usage
            saucenao_usage = {
                "short": results.short_remaining,
                "long": results.long_remaining
            }

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
                ]), quote=source.id)
                I_RUNING = False
            else:
                await app.sendGroupMessage(group, MessageChain.create([
                    Plain("\n==================\n".join(results_list))
                ]), quote=source.id)
                I_RUNING = False
        else:
            await app.sendGroupMessage(group, MessageChain.create([
                At(member.id),
                Plain(" 你的游戏币不足，无法使用")
            ]))


@channel.use(ListenerSchema(listening_events=[FriendMessage],
                            inline_dispatchers=[Literature("查看搜图用量")]))
async def check_saucenao(app: Ariadne, friend: Friend):
    if friend.id == yaml_data['Basic']['Permission']['Master']:
        global saucenao_usage
        if not saucenao_usage:
            async with AIOSauceNao(yaml_data['Saya']['AnimeSceneSearch']['saucenao_key']) as snao:
                results = await snao.from_url('https://i.imgur.com/oZjCxGo.jpg')
            saucenao_usage = {
                "short": results.short_remaining,
                "long": results.long_remaining
            }
        await app.sendFriendMessage(friend, MessageChain.create([
            Plain(f"当前用量：\n短期：{saucenao_usage['short']}\n长期：{saucenao_usage['long']}")
        ]))
