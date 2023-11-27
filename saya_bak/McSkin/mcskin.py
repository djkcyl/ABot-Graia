import re
import json
import httpx
import base64

from PIL import Image
from io import BytesIO

from util.browser import get_browser


class MinecraftSkin:
    def __init__(self, name) -> None:
        self.url = f"https://api.mojang.com/users/profiles/minecraft/{name}"
        self.name = name
        self.uuid = None

    async def get_uuid(self) -> str:
        if self.uuid:
            return self.uuid
        async with httpx.AsyncClient() as client:
            uuid = await client.get(self.url)
            self.uuid = uuid.json()["id"]
            return self.uuid

    async def get_skin(self) -> dict:
        async with httpx.AsyncClient() as client:
            skin = await client.get(
                f"https://sessionserver.mojang.com/session/minecraft/profile/{await self.get_uuid()}"
                + "?unsigned=false"
            )
            skin = base64.b64decode(skin.json()["properties"][0]["value"])
            return json.loads(skin)

    async def get_texture(self) -> str:
        skin = await self.get_skin()
        return skin["textures"]["SKIN"]["url"]

    async def get_cape(self) -> str:
        skin = await self.get_skin()
        return skin["textures"]["CAPE"]["url"]

    async def get_avatar(self):
        texture = await self.get_texture()
        async with httpx.AsyncClient() as client:
            resp = await client.get(texture)
        texture_image = Image.open(BytesIO(resp.content))
        avatar_image = texture_image.crop((8, 8, 8 + 8, 8 + 8))
        avatar_image = avatar_image.resize((100, 100), Image.NEAREST)
        avatar_image.save(bio := BytesIO(), format="PNG")
        return bio.getvalue()

    async def get_head_rander(self):
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://crafatar.com/renders/head/{await self.get_uuid()}?scale=10"
            )
        return resp.content

    async def get_body_rander(self):
        browser = await get_browser()
        page = await browser.new_page()
        await page.goto(
            f"https://zh-cn.namemc.com/profile/{self.name}", wait_until="domcontentloaded"
        )
        page_body = await page.content()
        uid = re.search("face\.png\?id=(.*?)&", page_body)[1]
        model = re.search(r"model=(.*?)&", page_body)[1]
        resp = await page.goto(
            f"https://s.namemc.com/3d/skin/body.png?id={uid}&width=380&height=720&model={model}&shadow_color=000&shadow_radius=18"
        )
        await resp.finished()
        pic = await resp.body()
        await page.close()
        return pic
