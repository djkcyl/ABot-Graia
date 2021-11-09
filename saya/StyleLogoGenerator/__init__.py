from io import BytesIO
from graia.saya import Saya, Channel
from graia.ariadne.model import Group
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.element import Plain, Image
from graia.ariadne.message.parser.pattern import RegexMatch
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.ariadne.message.parser.twilight import Twilight, Sparkle

from config import yaml_data, group_data
from util.sendMessage import safeSendGroupMessage
from util.control import Permission, Interval, Rest


from .Pornhub import PornhubStyleUtils
from .Youtube import YoutubeStyleUtils
from .GoSenChoEnHoShi import genImage as gsGenImage

LEFT_PART_VERTICAL_BLANK_MULTIPLY_FONT_HEIGHT = 2
LEFT_PART_HORIZONTAL_BLANK_MULTIPLY_FONT_WIDTH = 1 / 4
RIGHT_PART_VERTICAL_BLANK_MULTIPLY_FONT_HEIGHT = 1
RIGHT_PART_HORIZONTAL_BLANK_MULTIPLY_FONT_WIDTH = 1 / 4
RIGHT_PART_RADII = 10
BG_COLOR = '#000000'
BOX_COLOR = '#F7971D'
LEFT_TEXT_COLOR = '#FFFFFF'
RIGHT_TEXT_COLOR = '#000000'
FONT_SIZE = 50

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Twilight(Sparkle([RegexMatch("5000兆 .* .*")]))],
                            decorators=[Rest.rest_control(), Permission.require(), Interval.require()]))
async def gosencho_handler(message: MessageChain, group: Group):

    if yaml_data['Saya']['StyleLogoGenerator']['Disabled']:
        return
    elif 'StyleLogoGenerator' in group_data[str(group.id)]['DisabledFunc']:
        return

    await safeSendGroupMessage(group, await StylePictureGeneraterHandler.gosencho_en_hoshi_style_image_generator(message))


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Twilight(Sparkle([RegexMatch("ph .* .*")]))],
                            decorators=[Rest.rest_control(), Permission.require(), Interval.require()]))
async def pornhub_handler(message: MessageChain, group: Group):

    if yaml_data['Saya']['StyleLogoGenerator']['Disabled']:
        return
    elif 'StyleLogoGenerator' in group_data[str(group.id)]['DisabledFunc']:
        return

    await safeSendGroupMessage(group, await StylePictureGeneraterHandler.pornhub_style_image_generator(message))


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Twilight(Sparkle([RegexMatch("yt .* .*")]))],
                            decorators=[Rest.rest_control(), Permission.require(), Interval.require()]))
async def youtube_handler(message: MessageChain, group: Group):

    if yaml_data['Saya']['StyleLogoGenerator']['Disabled']:
        return
    elif 'StyleLogoGenerator' in group_data[str(group.id)]['DisabledFunc']:
        return

    await safeSendGroupMessage(group, await StylePictureGeneraterHandler.youtube_style_image_generator(message))


class StylePictureGeneraterHandler():
    """
    风格图片生成Handler
    """

    @staticmethod
    async def gosencho_en_hoshi_style_image_generator(message):
        try:
            _, left_text, right_text = message.asDisplay().split(" ")
            try:
                img_byte = BytesIO()
                gsGenImage(word_a=left_text, word_b=right_text).save(img_byte, format='PNG')
                return MessageChain.create([Image(data_bytes=img_byte.getvalue())])
            except TypeError:
                return MessageChain.create([Plain(text="不支持的内容！不要给我一些稀奇古怪的东西！")])
        except ValueError:
            return MessageChain.create([Plain(text="参数非法！使用格式：5000兆 text1 text2")])

    @staticmethod
    async def pornhub_style_image_generator(message):
        message_text = message.asDisplay()
        if '/' in message_text or '\\' in message_text:
            return MessageChain.create([Plain(text="不支持 '/' 与 '\\' ！")])
        try:
            _, left_text, right_text = message_text.split(" ")
        except ValueError:
            return MessageChain.create([Plain(text="格式错误！使用方法：ph left right!")])
        try:
            return await PornhubStyleUtils.make_ph_style_logo(left_text, right_text)
        except OSError as e:
            if "[Errno 22] Invalid argument:" in str(e):
                return MessageChain.create([Plain(text="非法字符！")])

    @staticmethod
    async def youtube_style_image_generator(message):
        message_text = message.asDisplay()
        if '/' in message_text or '\\' in message_text:
            return MessageChain.create([Plain(text="不支持 '/' 与 '\\' ！")])
        try:
            _, left_text, right_text = message_text.split(" ")
        except ValueError:
            return MessageChain.create([Plain(text="格式错误！使用方法：yt left right!")])
        try:
            return await YoutubeStyleUtils.make_yt_style_logo(left_text, right_text)
        except OSError as e:
            if "[Errno 22] Invalid argument:" in str(e):
                return MessageChain.create([Plain(text="非法字符！")])
