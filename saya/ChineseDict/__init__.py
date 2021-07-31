import os
import httpx
import base64

from lxml import etree
from graia.saya import Saya, Channel
from graia.application import GraiaMiraiApplication
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.event.messages import GroupMessage, Group
from graia.application.message.parser.literature import Literature
from graia.application.message.elements.internal import MessageChain, Plain, Image_LocalFile

from config import yaml_data, group_data, sendmsg

from .page_screenshot import get_hans_screenshot


TEMP_DIR = './saya/ChineseDict/temp'
if not os.path.exists(TEMP_DIR):
    print(f"检测到词典缓存文件夹不存在，正在创建")
    try:
        os.makedirs(TEMP_DIR)
    except:
        print(f"词典缓存文件夹创建失败！")
        exit()

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage], inline_dispatchers=[Literature("词典")]))
async def fun_dict(app: GraiaMiraiApplication, group: Group, message: MessageChain):

    if yaml_data['Saya']['ChineseDict']['Disabled']:
        return await sendmsg(app=app, group=group)
    elif 'ChineseDict' in group_data[group.id]['DisabledFunc']:
        return await sendmsg(app=app, group=group)

    saying = message.asDisplay().split()
    if len(saying) == 2:
        dict_name = saying[1]
        if not os.path.exists(f"{TEMP_DIR}/{dict_name}.jpg"):
            try:
                url = f"https://www.zdic.net/hans/{dict_name}"
                dict_html = httpx.get(url).text
                html = etree.HTML(dict_html, etree.HTMLParser())
                res_c_center_div_z = html.xpath(
                    "//div[@class='entry_title']/div[@class='ziif noi zisong']")
                res_c_center_div_c = html.xpath(
                    "//div[@class='entry_title']/div[@class='ciif noi zisong']")
                if res_c_center_div_z or res_c_center_div_c:
                    image_b64 = await get_hans_screenshot(url)
                    with open(f"{TEMP_DIR}/{dict_name}.jpg", "wb") as file:
                        image = base64.b64decode(image_b64)
                        file.write(image)
                    await app.sendGroupMessage(group, MessageChain.create([Image_LocalFile(f"{TEMP_DIR}/{dict_name}.jpg")]))
                    os.remove(f"{TEMP_DIR}/{dict_name}.jpg")
                else:
                    await app.sendGroupMessage(group, MessageChain.create([Plain(f"未找到该条目\n{dict_name}")]))
            except Exception as error:
                await app.sendGroupMessage(group, MessageChain.create([Plain(f"截图创建失败\n{error}")]))
                os.remove(f"{TEMP_DIR}/{dict_name}.jpg")
        else:
            await app.sendGroupMessage(group, MessageChain.create([Image_LocalFile(f"{TEMP_DIR}/{dict_name}.jpg")]))
