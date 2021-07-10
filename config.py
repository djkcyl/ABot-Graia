import yaml

from graia.application import GraiaMiraiApplication
from graia.application.event.messages import Group
from graia.application.message.elements.internal import MessageChain, Plain


async def sendmsg(app: GraiaMiraiApplication, group: Group):
    await app.sendGroupMessage(group, MessageChain.create([Plain("该功能暂不开启")]))


with open('config.yaml', 'r', encoding="utf-8") as f:
    file_data = f.read()
yaml_data = yaml.load(file_data)

if not bool(yaml_data['Final']):
    print("配置文件未修改完成，请手动编辑 config.exp.ymal 进行修改并重命名为 config.yaml")
    exit()
