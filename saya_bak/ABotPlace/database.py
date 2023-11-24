import datetime
from pathlib import Path
from graia.ariadne.model import Member, Group

from peewee import (
    Model,
    IntegerField,
    DateTimeField,
    SqliteDatabase,
    BigIntegerField,
)


db = SqliteDatabase(Path(__file__).parent.joinpath("PlaceSave.db"))


class BaseModel(Model):
    class Meta:
        database = db


# 画板历史记录
class PlaceHistory(BaseModel):
    member = BigIntegerField()
    group = BigIntegerField()
    time = DateTimeField(default=datetime.datetime.now)
    old_color = IntegerField()
    new_color = IntegerField()
    chunk_x = IntegerField()
    chunk_y = IntegerField()
    pixel_x = IntegerField()
    pixel_y = IntegerField()

    class Meta:
        db_table = "place_history"


db.create_tables([PlaceHistory], safe=True)


# 填充新像素
def fill_pixel(
    member: Member,
    group: Group,
    new_color: int,
    chunk_x: int,
    chunk_y: int,
    pixel_x: int,
    pixel_y: int,
):
    if old_pixel := PlaceHistory.get_or_none(
        PlaceHistory.chunk_x == chunk_x,
        PlaceHistory.chunk_y == chunk_y,
        PlaceHistory.pixel_x == pixel_x,
        PlaceHistory.pixel_y == pixel_y,
    ):
        old_color = old_pixel.new_color
    else:
        old_color = 1

    new_pixel = PlaceHistory.create(
        member=member.id,
        group=group.id,
        old_color=old_color,
        new_color=new_color,
        chunk_x=chunk_x,
        chunk_y=chunk_y,
        pixel_x=pixel_x,
        pixel_y=pixel_y,
    )
    return new_pixel.id
