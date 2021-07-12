import os
import yaml

from graia.application import GraiaMiraiApplication
from graia.application.event.messages import Group
from graia.application.message.elements.internal import MessageChain, Plain


async def sendmsg(app: GraiaMiraiApplication, group: Group):
    await app.sendGroupMessage(group, MessageChain.create([Plain("该功能暂不开启")]))

if not os.path.exists('config.yaml') and os.path.exists('config.exp.yaml'):
    print('请将 config.exp.yaml 重命名为 config.yaml ！')
    print('请将 config.exp.yaml 重命名为 config.yaml ！')
    print('请将 config.exp.yaml 重命名为 config.yaml ！')
    exit()
    
with open('config.yaml', 'r', encoding="utf-8") as f:
    file_data = f.read()
yaml_data = yaml.load(file_data)

if not bool(yaml_data['Final']):
    print("配置文件未修改完成，请手动编辑 config.exp.ymal 进行修改并重命名为 config.yaml")
    exit()

if yaml_data['Basic']['Permission']['Master'] not in yaml_data['Basic']['Permission']['Admin']:
    yaml_data['Basic']['Permission']['Admin'].append(yaml_data['Basic']['Permission']['Master'])
    with open("config.yaml", 'w', encoding="utf-8") as f:
        yaml.dump(yaml_data, f, allow_unicode=True)
    print("管理员内未包含主人，已自动添加")