import httpx


from graia.application import GraiaMiraiApplication


from config import yaml_data
from .get_proxy import get_proxy, next_proxy


head = {
    'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
    'Referer': 'https://www.bilibili.com/'
}


async def dynamic_svr(uid, app: GraiaMiraiApplication):
    for retry in range(3):
        try:
            async with httpx.AsyncClient(proxies=get_proxy(), headers=head) as client:
                r = await client.get(f"https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/space_history?host_uid={uid}")
        except httpx.HTTPError as e:
            app.logger.error(f"[BiliBili推送] API 访问失败，正在第 {retry + 1} 重试 {str(type(e))}")
            pass
        else:
            if r.status_code == 412:
                if yaml_data["Saya"]["BilibiliDynamic"]["EnabledProxy"]:
                    app.logger.error("[BiliBili推送] IP 已被封禁，更换代理后重试")
                    next_proxy()
                else:
                    return app.logger.error("[BiliBili推送] IP 已被封禁，本轮更新终止，请尝试使用代理")
            else:
                return r.json()
    else:
        app.logger.error("[BiliBili推送] API 访问连续失败，请检查")
        return


async def get_status_info_by_uids(uids, app: GraiaMiraiApplication):
    for retry in range(3):
        try:
            async with httpx.AsyncClient(proxies=get_proxy(), headers=head) as client:
                r = await client.post("https://api.live.bilibili.com/room/v1/Room/get_status_info_by_uids", json=uids)
        except httpx.HTTPError as e:
            app.logger.error(f"[BiliBili推送] API 访问失败，正在第 {retry + 1} 重试 {str(type(e))}")
            pass
        else:
            if r.status_code == 412:
                if yaml_data["Saya"]["BilibiliDynamic"]["EnabledProxy"]:
                    app.logger.error("[BiliBili推送] IP 已被封禁，更换代理后重试")
                    next_proxy()
                else:
                    return app.logger.error("[BiliBili推送] IP 已被封禁，本轮更新终止，请尝试使用代理")
            else:
                return r.json()
    else:
        app.logger.error("[BiliBili推送] API 访问连续失败，请检查")
        return
