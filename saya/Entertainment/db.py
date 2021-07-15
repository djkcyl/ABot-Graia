import datetime

from peewee import *
from graia.application.message.elements.internal import Plain

db = SqliteDatabase('./saya/Entertainment/userData.db')


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    qq = CharField(primary_key=True)
    nick = CharField()
    last_sign = IntegerField(default=0)
    gold = IntegerField(default=0)

    class Meta:
        table_name = 'user'


db.create_tables([User], safe=True)


async def sign(qq):
    user = User.get(User.qq == str(qq))
    if user.exists():
        user = User.get(username=User)