import httpx


async def time_parser(timestr: str) -> str:
    url = "http://a60.one:8010/time_parser"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params={"data": timestr})
        data = resp.json()["data"]
        if len(data) != 1:
            return False
        elif "detail" not in data[0]:
            return False
        elif "time" not in data[0]["detail"]:
            return False
        else:
            return data[0]["detail"]["time"][0]
