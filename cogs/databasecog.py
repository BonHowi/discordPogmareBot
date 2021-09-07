import inspect
from discord.ext import commands, tasks
from modules.get_settings import get_settings
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, Date, BigInteger
from sqlalchemy import create_engine, UniqueConstraint
from sqlalchemy.dialects.mysql import insert
import cogs.cogbase as cogbase

metadata_obj = MetaData()
member = Table('member', metadata_obj,
               Column('id', BigInteger, primary_key=True),
               Column('name', String(50), nullable=False),
               Column('display_name', String(50), nullable=False)
               )

spots = Table('spots', metadata_obj,
              Column('member_id', BigInteger, ForeignKey("member.id"), primary_key=True),
              Column('legendary', Integer),
              Column('rare', Integer),
              Column('common', Integer)
              )

spots_temp = Table('spots_temp', metadata_obj,
                   Column('member_id', BigInteger, ForeignKey("member.id"), primary_key=True),
                   Column('legendary', Integer),
                   Column('rare', Integer),
                   Column('common', Integer)
                   )

warn = Table('warn', metadata_obj,
             Column('id', Integer, primary_key=True),
             Column('member_id', BigInteger, ForeignKey("member.id")),
             Column('warn', String(50), nullable=False),
             Column('Date', Date, nullable=False),
             UniqueConstraint("member_id")
             )

coords = Table('coords', metadata_obj,
               Column('id', Integer, primary_key=True),
               Column('coords', String(50), nullable=False),
               )


class DatabaseCog(cogbase.BaseCog):
    def __init__(self, base):
        super().__init__(base)

        # Connect to database
        password = get_settings("DB_P")
        self.engine = create_engine(f"mysql+mysqldb://BonHow:{password}@localhost/server_database")
        metadata_obj.create_all(self.engine)
        self.conn = self.engine.connect()
        self.db_update_loop.start()

    # Add or refresh all guild members to database
    async def db_update(self):
        print(f"[{self.__class__.__name__}]:\t"
              f"{inspect.stack()[0][3]}: Refreshing member count")
        guild = self.bot.get_guild(self.bot.guild[0])
        for guild_member in guild.members:
            stmt = insert(member).values(
                id=guild_member.id, name=guild_member.name,
                display_name=guild_member.display_name)
            do_update_stmt = stmt.on_duplicate_key_update(
                name=stmt.inserted.name, display_name=stmt.inserted.display_name
            )
            self.conn.execute(do_update_stmt)

    @tasks.loop(hours=12)
    async def db_update_loop(self):
        await self.db_update()

    @db_update_loop.before_loop
    async def before_db_update(self):
        print(f'[{self.__class__.__name__}]: Waiting until Bot is ready')
        await self.bot.wait_until_ready()

    @db_update_loop.after_loop
    async def on_db_update_cancel(self):
        print(f"[{self.__class__.__name__}]: Placeholder for future improvements")


def setup(bot: commands.Bot):
    bot.add_cog(DatabaseCog(bot))
