import inspect
from discord.ext import commands, tasks
from modules.get_settings import get_settings
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, \
    BigInteger, update, select, DateTime, delete
from sqlalchemy.dialects.mysql import insert
import cogs.cogbase as cogbase
from datetime import datetime
import pandas as pd

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
             Column('reason', String(120), nullable=False),
             Column('date', DateTime, nullable=False),
             )

coords = Table('coords', metadata_obj,
               Column('id', Integer, primary_key=True),
               Column('coords', String(50), nullable=False),
               Column('monster_type', String(50), nullable=False)
               )


class DatabaseCog(cogbase.BaseCog):
    password = get_settings("DB_P")
    engine = create_engine(f"mysql+mysqldb://BonHowi:{password}@localhost/server_database")
    metadata_obj.create_all(engine)
    conn = engine.connect()

    def __init__(self, base):
        super().__init__(base)

        # Connect to database
        password = get_settings("DB_P")
        self.engine = create_engine(f"mysql+mysqldb://BonHowi:{password}@localhost/server_database")
        metadata_obj.create_all(self.engine)
        self.conn = self.engine.connect()
        self.db_update_loop.start()

    # ----- BASE DATABASE OPERATIONS -----

    def db_add_update_member(self, _member):
        stmt = insert(member).values(
            id=_member.id, name=_member.name,
            display_name=_member.display_name)
        do_update_stmt = stmt.on_duplicate_key_update(
            name=stmt.inserted.name, display_name=stmt.inserted.display_name
        )
        self.conn.execute(do_update_stmt)

    def db_add_update_spots(self, spots_table, guild_member):
        stmt = insert(spots_table).values(
            member_id=guild_member.id, legendary=0,
            rare=0, common=0)
        do_update_stmt = stmt.on_duplicate_key_update(member_id=stmt.inserted.member_id)
        self.conn.execute(do_update_stmt)

    # Add or refresh all guild members and spots to database
    async def db_update(self):
        guild = self.bot.get_guild(self.bot.guild[0])
        # Member tables
        print(f"[{self.__class__.__name__}]: Refreshing member count")
        for guild_member in guild.members:
            self.db_add_update_member(guild_member)
        print(f"[{self.__class__.__name__}]: Member count refreshed")

        # Spots tables
        guild = self.bot.get_guild(self.bot.guild[0])
        for guild_member in guild.members:
            self.db_add_update_spots(spots, guild_member)
            self.db_add_update_spots(spots_temp, guild_member)

    @tasks.loop(hours=12)
    async def db_update_loop(self):
        await self.db_update()

    @db_update_loop.before_loop
    async def before_db_update_loop(self):
        print(f'[{self.__class__.__name__}]: Waiting until Bot is ready')
        await self.bot.wait_until_ready()

    # Placeholder for simpler function(now it updates whole tables instead of one row)
    @commands.Cog.listener()
    async def on_member_join(self, _member):
        self.db_add_update_member(_member)
        self.db_add_update_spots(spots, _member)
        self.db_add_update_spots(spots_temp, _member)

    # ----- SPOTTING OPERATIONS -----

    @classmethod
    async def db_count_spot(cls, _id: int, monster_type: str):
        # Get member nr of spots for certain monster type
        stmt = select(spots.c.member_id, spots.c.legendary, spots.c.rare, spots.c.common).where(
            spots.c.member_id == _id)
        result = cls.conn.execute(stmt)
        counter = []
        for nr_of_kills in result.columns(monster_type):
            counter = nr_of_kills[0]
        stmt = update(spots).where(spots.c.member_id == _id).values({f"{monster_type}": counter + 1})
        cls.conn.execute(stmt)

        stmt = select(spots_temp.c.member_id, spots_temp.c.legendary, spots_temp.c.rare, spots_temp.c.common).where(
            spots_temp.c.member_id == _id)
        result = cls.conn.execute(stmt)
        for nr_of_kills in result.columns(monster_type):
            counter = nr_of_kills[0]
        stmt = update(spots_temp).where(spots_temp.c.member_id == _id).values({f"{monster_type}": counter + 1})
        cls.conn.execute(stmt)

    @classmethod
    async def db_save_coords(cls, _coords: str, _monster_type):
        stmt = insert(coords).values(coords=_coords, monster_type=_monster_type)
        cls.conn.execute(stmt)

    @classmethod
    async def db_clear_spots_temp_table(cls):
        stmt = delete(spots_temp)
        cls.conn.execute(stmt)

    # ----- LEADERBOARD OPERATIONS -----

    @classmethod
    async def db_get_spots_df(cls):
        stmt = select(member.c.display_name, spots.c.legendary, spots.c.rare, spots.c.common).select_from(member).join(
            spots,
            member.c.id == spots.c.member_id)
        df = pd.read_sql(stmt, cls.conn)
        return df

    async def db_update_spotting_roles(self):
        pass

    # ----- WARN OPERATIONS -----

    @classmethod
    async def db_add_warn(cls, _member: int, _reason: str):
        stmt = insert(warn).values(member_id=_member, reason=_reason, date=datetime.now())
        cls.conn.execute(stmt)

    @classmethod
    async def db_get_warns(cls, _member: int):
        stmt = select(warn.c.reason, warn.c.date).select_from(member).join(warn, member.c.id == warn.c.member_id).where(
            member.c.id == _member)
        result = cls.conn.execute(stmt)
        date_warn = []
        counter = 0
        for warns in result.columns("reason", "date"):
            reason_with_date = [warns[1], warns[0]]
            date_warn.append(reason_with_date)
            counter += 1
        warns_list = [': \t'.join([str(elem) for elem in sublist]) for sublist in date_warn]
        return warns_list, counter

    @classmethod
    async def db_remove_warns(cls, _member: int):
        stmt = delete(warn).where(warn.c.member_id == _member)
        cls.conn.execute(stmt)

    # ----- MEMBER OPERATIONS -----

    @classmethod
    async def db_get_member_stats(cls, _member: int):
        stmt = select(member.c.display_name, spots.c.legendary, spots.c.rare, spots.c.common).select_from(member).join(
            spots,
            member.c.id == spots.c.member_id).where(spots.c.member_id == _member)
        df = pd.read_sql(stmt, cls.conn)
        return df


def setup(bot: commands.Bot):
    bot.add_cog(DatabaseCog(bot))
