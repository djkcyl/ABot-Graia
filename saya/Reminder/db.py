from pathlib import Path
from datetime import datetime

from peewee import (
    BigIntegerField,
    SqliteDatabase,
    Model,
    DateTimeField,
    BooleanField,
    TextField,
)


database = SqliteDatabase(Path(__file__).parent.joinpath("reminder.db"))


class BaseModel(Model):
    class Meta:
        database = database


class Reminder(BaseModel):
    member = BigIntegerField()
    group = BigIntegerField()
    start_date = DateTimeField(default=datetime.now)
    end_date = DateTimeField()
    thing = TextField()
    completed = BooleanField(default=False)
    isdeleted = BooleanField(default=False)


database.create_tables([Reminder], safe=True)


def add_reminder(member, group, end_date, thing) -> int:
    thing = Reminder(member=member, group=group, end_date=end_date, thing=thing)
    thing.save()
    return thing.id


def get_undone_reminder() -> list[Reminder]:
    return Reminder.select().where(
        Reminder.isdeleted == 0,
        Reminder.completed == 0,
        Reminder.end_date < datetime.now(),
    )


def set_reminder_completed(id: int) -> None:
    Reminder.update(completed=True).where(Reminder.id == id).execute()
