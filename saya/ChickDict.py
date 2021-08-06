import requests

from graia.saya import Saya, Channel
from graia.application.group import Group, Member
from graia.application import GraiaMiraiApplication
from graia.application.event.messages import GroupMessage
from graia.saya.builtins.broadcast.schema import ListenerSchema
from graia.application.message.parser.literature import Literature
from graia.application.message.elements.internal import MessageChain, Plain, At, Image_NetworkAddress

from config import yaml_data, group_data, sendmsg
from util.limit import member_limit_check
from util.RestControl import rest_control

saya = Saya.current()
channel = Channel.current()


@channel.use(ListenerSchema(listening_events=[GroupMessage],
                            inline_dispatchers=[Literature("查梗")],
                            headless_decorators=[rest_control(), member_limit_check(30)]))
async def fun_dict(app: GraiaMiraiApplication, group: Group, message: MessageChain, member: Member):

    if yaml_data['Saya']['ChickDict']['Disabled']:
        return await sendmsg(app=app, group=group)
    elif 'ChickDict' in group_data[group.id]['DisabledFunc']:
        return await sendmsg(app=app, group=group)

    saying = message.asDisplay().split(" ", 1)
    if len(saying) != 2:
        await app.sendGroupMessage(group, MessageChain.create([
            Plain(f"用法：查梗 xxxxx")
        ]))
        return
    else:
        say_name = saying[1]
    if yaml_data['Basic']['Permission']['MasterName'].replace(" ", "").upper() in say_name.replace(" ", "").upper() or yaml_data['Basic']['BotName'].replace(" ", "").upper() in say_name.replace(" ", "").upper():
        await app.sendGroupMessage(group, MessageChain.create([
            At(member.id),
            Plain(f" 爬")
        ]))
        return

    # 数据请求
    api_url = "https://api.jikipedia.com/go/search_definitions"
    api_data = {
        "page": 1,
        "phrase": say_name
    }
    api_headers = {
        "Client": "web",
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": "https://jikipedia.com"
    }
    r_fun = requests.post(
        api_url,
        json=api_data,
        headers=api_headers).json()

    # 数据处理
    # 如果列表为空
    if "size" not in r_fun:
        await app.sendGroupMessage(group, MessageChain.create([
            Plain(f"API 访问错误"),
        ]))
    elif r_fun["size"] == 0:
        await app.sendGroupMessage(group, MessageChain.create([
            Plain(f"未找到相应词条：{say_name}"),
        ]))
    else:
        # 循环 “data” 内所有项目
        for r_fun_data in r_fun["data"]:
            r_fun_title = r_fun_data["term"]["title"]
            # 如果标题为所需查询内容
            if say_name == r_fun_title:
                r_fun_tags = "标签：无"
                r_fun_text = r_fun_data["plaintext"]
                tags = []
                tag_num = 0
                # 循环标签
                for t in r_fun_data["tags"]:
                    tags.append(t["name"])
                    tag_num = tag_num + 1
                if tag_num != 0:
                    r_fun_tags = f"标签：" + " | ".join(tags)
                msg_text = f"词条：{r_fun_title}\n{r_fun_tags}\n----------------------\n{r_fun_text}\n"
                msg_chain = [Plain(msg_text)]
                # 循环添加图片
                for image in r_fun_data["images"]:
                    msg_chain.append(Image_NetworkAddress(image["full"]["path"]))
                msg_chain.append(
                    Plain("----------------------\n数据来源为小鸡词典\nhttps://jikipedia.com/\n如果发现任何有问题的词条，与本bot无关，请前往小鸡词典官网反馈。"))
                await app.sendGroupMessage(group, MessageChain.create(msg_chain))
                break
        # 如本次请求列表内未找到相同标题内容
        else:
            r_fun_titles = []
            n = 1
            for r_fun_data in r_fun["data"]:
                r_fun_titles.append(r_fun_data["term"]["title"])
                if n > 20:
                    break
                n += 1
            await app.sendGroupMessage(str(group.id), MessageChain.create([
                Plain(f"未找到相应词条：{say_name}"),
                Plain(f"\n你可能要找？\n --->" + "\n --->".join(r_fun_titles)),
                Plain(f"\n数据来源为小鸡词典\nhttps://jikipedia.com/"),
                Plain(f"\n如果发现任何有问题的词条，与本bot无关，请前往小鸡词典官网反馈。")
            ]))
