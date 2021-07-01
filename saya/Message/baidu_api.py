import requests
import json


def img_censor(image_url, token):
    request_url = "https://aip.baidubce.com/rest/2.0/solution/v1/img_censor/v2/user_defined?access_token=" + token
    params = {"imgUrl": image_url}
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    r = requests.post(request_url, json=params, headers=headers).text
    result = json.loads(r)
    print(result)
    return result


def text_censor(text_str, token):
    print("正在审核")
    request_url = "https://aip.baidubce.com/rest/2.0/solution/v1/text_censor/v2/user_defined?access_token=" + token
    params = {"text": text_str}
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    r = requests.post(request_url, json=params, headers=headers).text
    result = json.loads(r)
    print(result)
    return result
