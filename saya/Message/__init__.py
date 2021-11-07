from pathlib import Path
from graia.saya import Saya, Channel
from graia.ariadne.model import Group
from graia.ariadne.app import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.broadcast.interrupt import InterruptControl
from graia.ariadne.message.element import Plain, Image
from graia.saya.builtins.broadcast.schema import ListenerSchema

from config import yaml_data, group_data
from util.control import Interval, Permission


saya = Saya.current()
channel = Channel.current()
bcc = saya.broadcast
inc = InterruptControl(bcc)

HOME = Path(__file__).parent


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            decorators=[Permission.require(), Interval.require(3, silent=True)]))
async def az(app: Ariadne, group: Group, message: MessageChain):

    if yaml_data['Saya']['Message']['Disabled']:
        return
    elif 'Message' in group_data[str(group.id)]['DisabledFunc']:
        return

    saying = message.asDisplay()
    if saying == "草":
        await app.sendGroupMessage(group, MessageChain.create([
            Plain("一种植物（")
        ]))
    if saying == "好耶":
        await app.sendGroupMessage(group, MessageChain.create([
            Image(path=HOME.joinpath("haoye.png"))
        ]))
    if saying == "流汗黄豆.jpg":
        await app.sendGroupMessage(group, MessageChain.create([
            Image(path=HOME.joinpath("jpg"))
        ]))
