import httpx
import base64

from .signer import TencentCloudSigner


class TencentCloudClient:
    def __init__(self, signer: TencentCloudSigner):
        self.signer = signer

    async def _get(self, baseurl, action, params: dict):
        headers = self.signer.get_headers(baseurl, action, params, "GET")
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://{baseurl}", headers=headers, params=params)
        return response.json()

    async def _post(self, baseurl, action, data: dict):
        headers = self.signer.get_headers(baseurl, action, data, "POST")
        async with httpx.AsyncClient() as client:
            response = await client.post(f"https://{baseurl}", headers=headers, json=data)
            print(response.text)
        return response.json()

    async def tms(self, content: str, userid: str):
        """
        文本内容安全

        :param content: 文本内容
        :param userid: 用户id
        """
        from .model.tms import TMSResponseModel

        params = {
            "Content": str(base64.b64encode(content.encode("utf-8")), "utf-8"),
            "User": {"UserId": userid},
        }
        return TMSResponseModel(
            **await self._post("tms.tencentcloudapi.com", "TextModeration", params)
        )

    async def ims(self, content: bytes | str, userid: str):
        """
        图片内容安全

        :param content: 图片内容
        :param userid: 用户id
        """
        from .model.ims import IMSResponseModel

        params: dict = {"User": {"UserId": userid}, "Interval": 3, "MaxFrames": 50}
        if isinstance(content, bytes):
            params["FileContent"] = str(base64.b64encode(content), "utf-8")
        else:
            params["FileUrl"] = content

        return IMSResponseModel(
            **await self._post("ims.tencentcloudapi.com", "ImageModeration", params)
        )
