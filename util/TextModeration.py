import json
import base64
from tencentcloud.common import credential
from tencentcloud.tms.v20201229 import tms_client, models
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException

from config import yaml_data


async def text_moderation(text: str):

    text_base64 = str(base64.b64encode(text.encode('utf-8')), "utf-8")
    try:
        cred = credential.Credential(yaml_data["Basic"]["API"]["Tencent"]["secretId"],
                                     yaml_data["Basic"]["API"]["Tencent"]["secretKey"])
        httpProfile = HttpProfile()
        httpProfile.endpoint = "tms.tencentcloudapi.com"

        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        client = tms_client.TmsClient(cred, "ap-shanghai", clientProfile)

        req = models.TextModerationRequest()
        params = {
            "Content": text_base64,
            "BizType": "group_recall_text"
        }
        req.from_json_string(json.dumps(params))

        resp = client.TextModeration(req)
        return json.loads(resp.to_json_string())

    except TencentCloudSDKException as err:
        return err
