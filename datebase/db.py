from peewee import *

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
        sign_num = user.sign_num + 1
        p = User.update(is_sign=1, sign_num=sign_num).where(User.qq == qq)
        p.execute()
        return True


async def get_info(qq):
    init_user(qq)
    user = User.get(qq=qq)
    return [user.id, user.is_sign, user.sign_num, user.gold, user.talk_num]


async def add_gold(qq: str, num: int):
    init_user(qq)
    gold_num = User.get(qq=qq).gold
    gold_num += num
    p = User.update(gold=gold_num).where(User.qq == qq)
    p.execute()
    return True


async def reduce_gold(qq: str, num: int):
    init_user(qq)
    gold_num = User.get(qq=qq).gold
    if gold_num < num:
        return False
    else:
        gold_num -= num
        p = User.update(gold=gold_num).where(User.qq == qq)
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