import httpx

from lxml import etree
from graia.saya import Saya, Channel
from graia.ariadne.app import Ariadne
from graia.ariadne.model import Group
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Image
from graia.ariadne.message.parser.literature import Literature
from graia.saya.builtins.broadcast.schema import ListenerSchema

from config import yaml_data, group_data
from util.RestControl import rest_control
from util.limit import member_limit_check
from util.UserBlock import group_black_list_block

from .page_screenshot import get_hans_screenshot


saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Literature("词典")],
                            decorators=[rest_control(), member_limit_check(15), group_black_list_block()]))
async def dict(app: Ariadne, group: Group, message: MessageChain):

    if yaml_data['Saya']['ChineseDict']['Disabled']:
        return
    elif 'ChineseDict' in group_data[group.id]['DisabledFunc']:
        return

    saying = message.asDisplay().split()
    if len(saying) == 2:
        dict_name = saying[1]
        try:
            url = f"https://www.zdic.net/hans/{dict_name}"
            dict_html = httpx.get(url).text
            html = etree.HTML(dict_html, etree.HTMLParser())
            res_c_center_div_z = html.xpath(
                "//div[@class='entry_title']/div[@class='ziif noi zisong']")
            res_c_center_div_c = html.xpath(
                "//div[@class='entry_title']/div[@class='ciif noi zisong']")
            if res_c_center_div_z or res_c_center_div_c:
                image = await get_hans_screenshot(url)
                await app.sendGroupMessage(group, MessageChain.create([Image(data_bytes=image)]))
            else:
                await app.sendGroupMessage(group, MessageChain.create([Plain(f"未找到该条目\n{dict_name}")]))
        except Exception as error:
            await app.sendGroupMessage(group, MessageChain.create([Plain(f"截图创建失败\n{error}")]))
