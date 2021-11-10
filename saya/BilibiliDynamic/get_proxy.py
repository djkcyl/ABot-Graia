from config import yaml_data

proxys = []

if yaml_data["Saya"]["BilibiliDynamic"]["EnabledProxy"]:
    for proxy in yaml_data["Saya"]["BilibiliDynamic"]["Proxy"]:
        proxys.append({"all://": f"{proxy}"})
        print(proxy)
    proxy_count = len(yaml_data["Saya"]["BilibiliDynamic"]["Proxy"])
    print(f"当前共有 {proxy_count} 个代理")
else:
    proxys = [None]

proxy_index = 0


def next_proxy():
    global proxy_index
    if proxy_index == proxy_count:
        proxy_index = 0
    proxy_index += 1
    return proxys[proxy_index - 1]


def get_proxy():
    if yaml_data["Saya"]["BilibiliDynamic"]["EnabledProxy"]:
        return proxys[proxy_index - 1]
    else:
        return
