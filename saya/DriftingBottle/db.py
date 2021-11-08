import datetime

from pathlib import Path
from graia.ariadne.model import Member
from peewee import BigIntegerField, IntegerField, SqliteDatabase, Model, TextField, DateTimeField, fn


db = SqliteDatabase(Path(__file__).parent.joinpath('Bottlelibrary.db'))


class BaseModel(Model):
    class Meta:
        database = db


class DriftingBottle(BaseModel):
    member = BigIntegerField()
    group = BigIntegerField()
    text = TextField(null=True)
    image = TextField(null=True)
    fishing_times = IntegerField(default=0)
    send_date = DateTimeField(default=datetime.datetime.now)

    class Meta:
        db_table = 'bottle_list'


db.create_tables([DriftingBottle], safe=True)


def throw_bottle(sender: Member, text=None, image=None) -> int:
    bottle = DriftingBottle(member=sender.id, group=sender.group.id, text=text, image=image)
    bottle.save()
    return bottle.id


def get_bottle() -> dict:
    "随机捞一个瓶子"
    if DriftingBottle.select().count() == 0:
        return None
    else:
        bottle: DriftingBottle = DriftingBottle.select().order_by(fn.Random()).get()
        DriftingBottle.update(fishing_times=DriftingBottle.fishing_times + 1).where(DriftingBottle.id == bottle.id).execute()
        return {
            'id': bottle.id,
            'member': bottle.member,
            'group': bottle.group,
            'text': bottle.text,
            'image': bottle.image,
            'fishing_times': bottle.fishing_times,
            'send_date': bottle.send_date
        }


def get_bottle_by_id(bottle_id: int):
    return DriftingBottle.select().where(DriftingBottle.id == bottle_id).get()


def count_bottle() -> int:
    return DriftingBottle.select().count()


def clear_bottle():
    DriftingBottle.delete().execute()


def clear_bottle_by_member(member: Member):
    DriftingBottle.delete().where(DriftingBottle.member == member.id).execute()


def delete_bottle(bottle_id: int):
    DriftingBottle.delete().where(DriftingBottle.id == bottle_id).execute()
