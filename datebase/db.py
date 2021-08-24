import json
import httpx

from peewee import *
from prettytable import PrettyTable


db = SqliteDatabase('./datebase/userData.db')


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    qq = CharField()
    is_sign = IntegerField()
    sign_num = IntegerField()
    gold = IntegerField()
    talk_num = IntegerField()

    class Meta:
        table_name = 'user_info'


db.create_tables([User], safe=True)


def init_user(qq):
    user = User.select().where(User.qq == qq)
    if not user.exists():
        p = User(qq=qq, is_sign=0, sign_num=0, gold=0, talk_num=0)
        p.save()
        print("已初始化" + str(qq))


async def sign(qq):
    init_user(qq)
    user = User.get(qq=qq)
    if user.is_sign:
        return False
    else:
        p = User.update(is_sign=1, sign_num=User.sign_num+1).where(User.qq == qq)
        p.execute()
        return True


async def get_info(qq):
    init_user(qq)
    user = User.get(qq=qq)
    return [user.id, user.is_sign, user.sign_num, user.gold, user.talk_num]


async def add_gold(qq: str, num: int):
    init_user(qq)
    gold_num = User.get(qq=qq).gold
    p = User.update(gold=User.gold+num).where(User.qq == qq)
    p.execute()
    return True


async def reduce_gold(qq: str, num: int):
    init_user(qq)
    gold_num = User.get(qq=qq).gold
    if gold_num < num:
        return False
    else:
        p = User.update(gold=User.gold-num).where(User.qq == qq)
        p.execute()
        return True


async def add_talk(qq: str):
    init_user(qq)
    User.update(talk_num=User.talk_num+1).where(User.qq == qq).execute()
    return


async def reset_sign():
    User.update(is_sign=0).where(User.is_sign == 1).execute()
    return


async def all_sign_num():
    all_num = User.select()
    all_num = len(all_num)
    sign_num = User.select().where(User.is_sign == 1)
    sign_num = len(sign_num)
    return [sign_num, all_num]


async def give_all_gold(num: int):
    User.update(gold=User.gold+num).execute()
    return


async def get_ranking():
    user_list = User.select().order_by(User.gold.desc())
    user_num = len(user_list)
    gold_rank = PrettyTable()
    gold_rank.field_names = [" ID ", "      QQ      ", "         NICK         ", "  GOLD  ", "  TALK  ", "RANK"]
    gold_rank.align[" ID "] = "r"
    gold_rank.align["  GOLD  "] = "r"
    gold_rank.align["  TALK  "] = "r"
    gold_rank.align["RANK"] = "r"
    i = 1

    for user_info in user_list[:15]:
        user_id = user_info.id
        user_qq = user_info.qq

        async with httpx.AsyncClient() as client:
            r = await client.get(f"https://r.qzone.qq.com/fcg-bin/cgi_get_portrait.fcg?uins={user_qq}")
            r.encoding = 'GBK'
            qqdata = r.text

        qqdata = json.loads(qqdata[17:-1])
        user_nick = qqdata[user_qq][-2]

        # user_nick = await getCutStr(qqnick, 20)
        user_gold = user_info.gold
        user_talk = user_info.talk_num
        gold_rank.add_row([user_id, user_qq, user_nick, user_gold, user_talk, i])
        i += 1

    gold_rank = gold_rank.get_string()

    user_list = User.select().order_by(User.talk_num.desc())
    user_num = len(user_list)
    talk_rank = PrettyTable()
    talk_rank.field_names = [" ID ", "      QQ      ", "         NICK         ", "  GOLD  ", "  TALK  ", "RANK"]
    talk_rank.align[" ID "] = "r"
    talk_rank.align["  GOLD  "] = "r"
    talk_rank.align["  TALK  "] = "r"
    talk_rank.align["RANK"] = "r"
    i = 1

    for user_info in user_list[:15]:
        user_id = user_info.id
        user_qq = user_info.qq

        async with httpx.AsyncClient() as client:
            r = await client.get(f"https://r.qzone.qq.com/fcg-bin/cgi_get_portrait.fcg?uins={user_qq}")
            r.encoding = 'GBK'
            qqdata = r.text

        qqdata = json.loads(qqdata[17:-1])
        user_nick = qqdata[user_qq][-2]

        # user_nick = await getCutStr(qqnick, 20)
        user_gold = user_info.gold
        user_talk = user_info.talk_num
        talk_rank.add_row([user_id, user_qq, user_nick, user_gold, user_talk, i])
        i += 1

    talk_rank = talk_rank.get_string()
    return str(f"ABot 排行榜：\n当前共服务了 {user_num} 位用户\n游戏币排行榜\n{gold_rank}\n发言排行榜\n{talk_rank}")


async def getCutStr(str, cut):
    si = 0
    i = 0
    for s in str:
        if '\u4e00' <= s <= '\u9fff':
            si += 2
        else:
            si += 1
        i += 1
        if si > cut:
            cutStr = str[:i] + '....'
            break
        else:
            cutStr = str

    return cutStr
