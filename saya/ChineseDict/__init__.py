import httpx

from lxml import etree
from graia.saya import Saya, Channel
from graia.ariadne.model import Group
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, Image
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import Twilight, FullMatch, WildcardMatch

from util.sendMessage import safeSendGroupMessage
from util.control import Permission, Interval, Rest, Function

from .page_screenshot import get_hans_screenshot


saya = Saya.current()
channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight({"head": FullMatch("词典"), "anything": WildcardMatch()})
        ],
        decorators=[
            Function.require("ChineseDict"),
            Permission.require(),
            Rest.rest_control(),
            Interval.require(),
        ],
    )
)
async def dict(group: Group, anything: WildcardMatch):
    if anything.matched:
        dict_name = anything.result.asDisplay()
        try:
            url = f"https://www.zdic.net/hans/{dict_name}"
            dict_html = httpx.get(url).text
            html = etree.HTML(dict_html, etree.HTMLParser())
            res_c_center_div_z = html.xpath(
                "//div[@class='entry_title']/div[@class='ziif noi zisong']"
            )
            res_c_center_div_c = html.xpath(
                "//div[@class='entry_title']/div[@class='ciif noi zisong']"
            )
            if res_c_center_div_z or res_c_center_div_c:
                image = await get_hans_screenshot(url)
                await safeSendGroupMessage(
                    group, MessageChain.create([Image(data_bytes=image)])
                )
            else:
                await safeSendGroupMessage(
                    group, MessageChain.create([Plain(f"未找到该条目\n{dict_name}")])
                )
        except Exception as error:
            await safeSendGroupMessage(
                group, MessageChain.create([Plain(f"截图创建失败\n{error}")])
            )
