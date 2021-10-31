import os
import yaml
import json

from pathlib import Path


class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


if not os.path.exists('config.yaml') and os.path.exists('config.exp.yaml'):
    print('请修改 config.exp.yaml 并重命名为 config.yaml ！')
    print('请修改 config.exp.yaml 并重命名为 config.yaml ！')
    print('请修改 config.exp.yaml 并重命名为 config.yaml ！')
    exit()
elif not os.path.exists('config.yaml') and not os.path.exists('config.exp.yaml'):
    print('在？宁的配置文件呢?¿?¿')
    exit()
else:
    with open('config.yaml', 'r', encoding="utf-8") as f:
        file_data = f.read()
    yaml_data = yaml.load(file_data, Loader=yaml.FullLoader)

MIRAI_PATH = Path(yaml_data["Basic"]["MiraiPath"])
VIOCE_PATH = MIRAI_PATH.joinpath("data", "net.mamoe.mirai-api-http", "voices")
# if not VIOCE_PATH.exists():
#     print(f"{VIOCE_PATH} 不存在，请修改配置文件中的 Basic-MiraiPath 为Mirai的根目录")
#     exit()

if os.path.exists('groupdata.yaml'):
    with open('groupdata.yaml', 'r', encoding="utf-8") as f:
        file_data = f.read()
    group_data = yaml.load(file_data, Loader=yaml.FullLoader)
else:
    with open('groupdata.yaml', 'w', encoding="utf-8") as f:
        group_data = json.loads("{}")
        yaml.dump(group_data, f, allow_unicode=True, Dumper=NoAliasDumper)

if os.path.exists('grouplist.json'):
    with open('grouplist.json', 'r', encoding="utf-8") as f:
        group_list = json.load(f)
else:
    with open('grouplist.json', 'w', encoding="utf-8") as f:
        group_list = {
            "white": []
        }
        json.dump(group_list, f, indent=2)

if os.path.exists('userlist.json'):
    with open('userlist.json', 'r', encoding="utf-8") as f:
        user_list = json.load(f)
else:
    with open('userlist.json', 'w', encoding="utf-8") as f:
        user_list = {
            "black": []
        }
        json.dump(user_list, f, indent=2)

user_black_list = user_list['black']

if not bool(yaml_data['Final']):
    print("配置文件未修改完成，请手动编辑 config.exp.ymal 进行修改并重命名为 config.yaml")
    exit()

if yaml_data['Basic']['Permission']['Master'] not in yaml_data['Basic']['Permission']['Admin']:
    yaml_data['Basic']['Permission']['Admin'].append(yaml_data['Basic']['Permission']['Master'])
    with open("config.yaml", 'w', encoding="utf-8") as f:
        yaml.dump(yaml_data, f, allow_unicode=True)
    print("管理员内未包含主人，已自动添加")


def save_config():
    print("正在保存配置文件")
    with open("groupdata.yaml", 'w', encoding="utf-8") as f:
        yaml.dump(group_data, f, allow_unicode=True, Dumper=NoAliasDumper)
    with open("config.yaml", 'w', encoding="utf-8") as f:
        yaml.dump(yaml_data, f, allow_unicode=True, Dumper=NoAliasDumper)
    with open("grouplist.json", 'w', encoding="utf-8") as f:
        json.dump(group_list, f, indent=2)
    with open('userlist.json', 'w', encoding="utf-8") as f:
        json.dump(user_list, f, indent=2)


save_config()
