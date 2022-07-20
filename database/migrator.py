from playhouse.migrate import SqliteDatabase, SqliteMigrator, migrate, IntegerField

db = SqliteDatabase("./database/userData.db")
migrator = SqliteMigrator(db)

migrate(
    migrator.add_column("user_info", "is_chat", IntegerField(default=0)),
    migrator.add_column("user_info", "continue_sign", IntegerField(default=0)),
)
