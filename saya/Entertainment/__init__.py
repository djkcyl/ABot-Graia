from graia.saya import Saya, Channel
from graia.application.event.mirai import *
from graia.application.event.messages import *
from graia.application import GraiaMiraiApplication
from graia.application.message.elements.internal import *
from graia.saya.builtins.broadcast.schema import ListenerSchema

from config import yaml_data

from .db import sign

saya = Saya.current()
channel = Channel.current()


