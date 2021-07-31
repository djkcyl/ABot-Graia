import json
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.ims.v20201229 import ims_client, models


async def image_moderation(url: str):
    try: 
        cred = credential.Credential("SecretId", "SecretKey") 
        httpProfile = HttpProfile()
        httpProfile.endpoint = "ims.tencentcloudapi.com"

        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        client = ims_client.ImsClient(cred, "ap-shanghai", clientProfile) 

        req = models.ImageModerationRequest()
        params = {
            "FileUrl": url
        }
        req.from_json_string(json.dumps(params))

        resp = client.ImageModeration(req)
        return resp.to_json_string()

    except TencentCloudSDKException as err: 
        return err