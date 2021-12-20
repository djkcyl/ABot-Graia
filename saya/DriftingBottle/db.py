import datetime

from pathlib import Path
from graia.ariadne.model import Member
from peewee import (
    BigIntegerField,
    SqliteDatabase,
    Model,
    TextField,
    DateTimeField,
    BooleanField,
    IntegerField,
    fn,
)


db = SqliteDatabase(Path(__file__).parent.joinpath("Bottlelibrary.db"))


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
    isdelete = BooleanField(default=False)

    class Meta:
        db_table = "bottle_list"


class BottleScore(BaseModel):
    member = BigIntegerField()
    bottle_id = IntegerField()
    socre = IntegerField()

    class Meta:
        db_table = "bottle_score"


db.create_tables([DriftingBottle, BottleScore], safe=True)


def throw_bottle(sender: Member, text=None, image=None) -> int:
    bottle = DriftingBottle(
        member=sender.id, group=sender.group.id, text=text, image=image
    )
    bottle.save()
    return bottle.id


def get_bottle() -> dict:
    "随机捞一个瓶子"
    if DriftingBottle.select().count() == 0:
        return None
    else:
        bottle: DriftingBottle = (
            DriftingBottle.select()
            .where(DriftingBottle.isdelete == 0)
            .order_by(fn.Random())
            .get()
        )
        DriftingBottle.update(fishing_times=DriftingBottle.fishing_times + 1).where(
            DriftingBottle.id == bottle.id
        ).execute()
        return {
            "id": bottle.id,
            "member": bottle.member,
            "group": bottle.group,
            "text": bottle.text,
            "image": bottle.image,
            "fishing_times": bottle.fishing_times,
            "send_date": bottle.send_date,
        }


def get_bottle_by_id(bottle_id: int):
    return DriftingBottle.select().where(
        DriftingBottle.id == bottle_id, DriftingBottle.isdelete == 0
    )


def count_bottle() -> int:
    return DriftingBottle.select(DriftingBottle.isdelete == 0).count()


def clear_bottle():
    DriftingBottle.delete().execute()


def delete_bottle_by_member(member: Member):
    DriftingBottle.update(isdelete=True).where(
        DriftingBottle.member == member.id
    ).execute()


def delete_bottle(bottle_id: int):
    DriftingBottle.update(isdelete=True).where(DriftingBottle.id == bottle_id).execute()


# 漂流瓶评分系统

# 获取漂流瓶评分平均数，保留一位小数
def get_bottle_score_avg(bottle_id: int):
    if BottleScore.select().where(BottleScore.bottle_id == bottle_id).count() == 0:
        return False
    else:
        count = BottleScore.select().where(BottleScore.bottle_id == bottle_id).count()
        socre = 0
        for i in BottleScore.select(BottleScore.socre).where(
            BottleScore.bottle_id == bottle_id
        ):
            socre += i.socre

        return "%.1f" % (socre / count)


def add_bottle_score(bottle_id: int, member: Member, score: int):
    if 1 <= score <= 5:
        if (
            BottleScore.select()
            .where(BottleScore.bottle_id == bottle_id, BottleScore.member == member.id)
            .exists()
        ):
            return False
        else:
            BottleScore.create(bottle_id=bottle_id, member=member.id, socre=score)
            return True
