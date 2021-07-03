import yaml

from graia.application import GraiaMiraiApplication
from graia.application.event.messages import Group
from graia.application.message.elements.internal import MessageChain, Plain


file = open('config.yaml', 'r', encoding="utf-8")
file_data = file.read()
yaml_data = yaml.load(file_data)
file.close()


async def sendmsg(app: GraiaMiraiApplication, group: Group):
    await app.sendGroupMessage(group, MessageChain.create([Plain("该功能暂不开启")]))


class Config:
    class Basic:
        BotName = str(yaml_data['Basic']['BotName'])

        class MAH:
            BotQQ = int(yaml_data['Basic']['MAH']['BotQQ'])
            MiraiHost = str(yaml_data['Basic']['MAH']['MiraiHost'])

            MiraiAuthKey = str(yaml_data['Basic']['MAH']['MiraiAuthKey'])

        class Permission:
            Master = int(yaml_data['Basic']['Permission']['Master'])
            MasterName = str(yaml_data['Basic']['Permission']['MasterName'])
            Admin = list(yaml_data['Basic']['Permission']['Admin'])
            Admin.append(Master)

    class Saya:
        class AliTTS:
            Disabled = bool(yaml_data['Saya']['AliTTS']['Disabled'])
            Blacklist = list(yaml_data['Saya']['AliTTS']['Blacklist'])

            Appkey = str(yaml_data['Saya']['AliTTS']['Appkey'])

            class AccessKey:
                Id = str(yaml_data['Saya']['AliTTS']['AccessKey']['Id'])
                Secret = str(yaml_data['Saya']['AliTTS']
                             ['AccessKey']['Secret'])

        class ChickDict:
            Disabled = bool(yaml_data['Saya']['ChickDict']['Disabled'])
            Blacklist = list(yaml_data['Saya']['ChickDict']['Blacklist'])

        class ChickEmoji:
            Disabled = bool(yaml_data['Saya']['ChickEmoji']['Disabled'])
            Blacklist = list(yaml_data['Saya']['ChickEmoji']['Blacklist'])

        class ChineseDict:
            Disabled = bool(yaml_data['Saya']['ChineseDict']['Disabled'])
            Blacklist = list(yaml_data['Saya']['ChineseDict']['Blacklist'])

        class CloudMusic:
            Disabled = bool(yaml_data['Saya']['CloudMusic']['Disabled'])
            Blacklist = list(yaml_data['Saya']['CloudMusic']['Blacklist'])
            MusicInfo = bool(yaml_data['Saya']['CloudMusic']['MusicInfo'])

            class ApiConfig:
                PhoneNumber = str(
                    yaml_data['Saya']['CloudMusic']['ApiConfig']['PhoneNumber'])
                Password = str(
                    yaml_data['Saya']['CloudMusic']['ApiConfig']['Password'])

        class WordCloud:
            Disabled = bool(yaml_data['Saya']['WordCloud']['Disabled'])
            Blacklist = list(yaml_data['Saya']['WordCloud']['Blacklist'])

        class MutePack:
            Disabled = bool(yaml_data['Saya']['MutePack']['Disabled'])
            Blacklist = list(yaml_data['Saya']['MutePack']['Blacklist'])
            MaxTime = int(yaml_data['Saya']['MutePack']['MaxTime'])
            MaxMultiple = int(yaml_data['Saya']['MutePack']['MaxMultiple'])
            MaxJackpotProbability = int(
                yaml_data['Saya']['MutePack']['MaxJackpotProbability'])
            SuperDouble = bool(yaml_data['Saya']['MutePack']['SuperDouble'])
            MaxSuperDoubleProbability = int(
                yaml_data['Saya']['MutePack']['MaxSuperDoubleProbability'])
            MaxSuperDoubleMultiple = int(
                yaml_data['Saya']['MutePack']['MaxSuperDoubleMultiple'])

        class Beast:
            Disabled = bool(yaml_data['Saya']['Beast']['Disabled'])
            Blacklist = list(yaml_data['Saya']['Beast']['Blacklist'])
            BeastPhrase = list(yaml_data['Saya']['Beast']['BeastPhrase'])

        class MinecraftPing:
            Disabled = bool(yaml_data['Saya']['MinecraftPing']['Disabled'])
            Blacklist = list(yaml_data['Saya']['MinecraftPing']['Blacklist'])

        class PetPet:
            Disabled = bool(yaml_data['Saya']['PetPet']['Disabled'])
            Blacklist = list(yaml_data['Saya']['PetPet']['Blacklist'])
            CanAt = bool(yaml_data['Saya']['PetPet']['CanAt'])
            CanNudge = bool(yaml_data['Saya']['PetPet']['CanNudge'])

        class PornhubLogo:
            Disabled = bool(yaml_data['Saya']['PornhubLogo']['Disabled'])
            Blacklist = list(yaml_data['Saya']['PornhubLogo']['Blacklist'])

    Final = bool(yaml_data['Final'])


if not Config.Final:
    print("配置文件未修改完成，请手动编辑 config.exp.ymal 进行修改并重命名为 config.yaml")
    exit()
