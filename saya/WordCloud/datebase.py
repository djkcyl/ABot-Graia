from peewee import *

db = SqliteDatabase('./saya/WordCloud/Data.db')


class BaseModel(Model):
    class Meta:
        database = db


class UserTalk(BaseModel):
    qq = CharField()
    group = CharField()
    msg = TextField()

    class Meta:
        table_name = 'user_talk'


db.create_tables([UserTalk], safe=True)


async def add_talk(qq, group, msg):
    p = UserTalk(qq=qq, group=group, msg=msg)
    p.save()


async def get_user_talk(qq, group):
    talklist = UserTalk.select().where(UserTalk.qq == qq, UserTalk.group == group)
    talk_list = []
    for talk in talklist:
        talk_list.append(talk.msg)
    return talk_list


async def get_group_talk(group):
    talklist = UserTalk.select().where(UserTalk.group == group)
    talk_list = []
    for talk in talklist:
        talk_list.append(talk.msg)
    return talk_list
