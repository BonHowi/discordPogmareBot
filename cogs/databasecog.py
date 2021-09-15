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
fk_member_id = "member.id"

spots = Table('spots', metadata_obj,
              Column('member_id', BigInteger, ForeignKey(fk_member_id), primary_key=True),
              Column('legendary', Integer, default=0),
              Column('rare', Integer, default=0),
              Column('common', Integer, default=0),
              Column('event1', Integer, default=0),
              Column('event2', Integer, default=0)
              )

spots_temp = Table('spots_temp', metadata_obj,
                   Column('member_id', BigInteger, ForeignKey(fk_member_id), primary_key=True),
                   Column('legendary', Integer, default=0),
                   Column('rare', Integer, default=0),
                   Column('common', Integer, default=0),
                   Column('event1', Integer, default=0),
                   Column('event2', Integer, default=0)
                   )

warn = Table('warn', metadata_obj,
             Column('id', Integer, primary_key=True),
             Column('member_id', BigInteger, ForeignKey(fk_member_id)),
             Column('reason', String(120), nullable=False),
             Column('date', DateTime, nullable=False),
             )

coords = Table('coords', metadata_obj,
               Column('id', Integer, primary_key=True),
               Column('coords', String(100), nullable=False),
               Column('monster_type', String(20), nullable=False)
               )


# noinspection PyPropertyAccess
class DatabaseCog(cogbase.BaseCog):
    user = get_settings("DB_U")
    password = get_settings("DB_P")
    engine = create_engine(f"mysql+mysqldb://{user}:{password}@localhost/server_database?charset=utf8mb4")
    metadata_obj.create_all(engine)
    conn = None

    def __init__(self, base):
        super().__init__(base)

        # Connect to database
        self.engine = DatabaseCog.engine
        metadata_obj.create_all(self.engine)
        self.db_update_loop.start()
        self.conn = DatabaseCog.conn

    # ----- BASE DATABASE OPERATIONS -----

    # Add or update member in member table
    def db_add_update_member(self, _member):
        self.conn = self.engine.connect()
        stmt = insert(member).values(
            id=_member.id, name=_member.name,
            display_name=_member.display_name)
        do_update_stmt = stmt.on_duplicate_key_update(
            name=stmt.inserted.name, display_name=stmt.inserted.display_name
        )
        self.conn.execute(do_update_stmt)
        self.conn.close()

    # Add or update spots in spots table
    def db_add_update_spots(self, spots_table, guild_member):
        self.conn = self.engine.connect()
        stmt = insert(spots_table).values(
            member_id=guild_member.id)
        do_update_stmt = stmt.on_duplicate_key_update(member_id=stmt.inserted.member_id)
        self.conn.execute(do_update_stmt)
        self.conn.close()

    # Add or refresh all guild members and spots to database
    async def db_update(self):
        self.conn = self.engine.connect()
        guild = self.bot.get_guild(self.bot.guild[0])
        dt_string = self.bot.get_current_time()
        print(f"({dt_string})\t[{self.__class__.__name__}]: Refreshing member and spots tables")
        for guild_member in guild.members:
            # Member tables
            self.db_add_update_member(guild_member)
            # Spots tables
            self.db_add_update_spots(spots, guild_member)
            self.db_add_update_spots(spots_temp, guild_member)
        dt_string = self.bot.get_current_time()
        print(f"({dt_string})\t[{self.__class__.__name__}]: Member and spots tables refreshed")
        self.conn.close()

    @tasks.loop(hours=12)
    async def db_update_loop(self):
        await self.db_update()

    @db_update_loop.before_loop
    async def before_db_update_loop(self):
        dt_string = self.bot.get_current_time()
        print(f'({dt_string})\t[{self.__class__.__name__}]: Waiting until Bot is ready')
        await self.bot.wait_until_ready()

    # Add member to database on member join
    @commands.Cog.listener()
    async def on_member_join(self, _member):
        self.db_add_update_member(_member)
        self.db_add_update_spots(spots, _member)
        self.db_add_update_spots(spots_temp, _member)

    # # Command for loading data from previous bot
    # @cog_ext.cog_slash(name="updateSpotsWithOld", guild_ids=cogbase.GUILD_IDS,
    #                    description="Update db with old data",
    #                    permissions=cogbase.PERMISSION_ADMINS)
    # async def db_update_spots_old(self, ctx):
    #     self.conn = self.engine.connect()
    #     import json
    #     with open('server_files/old_base.json', 'r', encoding='utf-8-sig') as fp:
    #         old_db = json.load(fp)
    #     guild = self.bot.get_guild(self.bot.guild[0])
    #
    #     for mem_id in old_db:
    #         if guild.get_member(int(mem_id)) is None:
    #             continue
    #
    #         stmt = select(spots.c.member_id, spots.c.legendary, spots.c.rare, spots.c.common).where(
    #             spots.c.member_id == mem_id)
    #         result = self.conn.execute(stmt).fetchall()
    #         result = result[0]
    #         counter_lege = result[1]
    #         counter_rare = result[2]
    #         counter_common = result[3]
    #
    #         counter_lege_old = old_db[mem_id]["type_1"] if "type_1" in old_db[mem_id] else 0
    #         counter_rare_old = old_db[mem_id]["type_0"] if "type_0" in old_db[mem_id] else 0
    #         counter_common_old = old_db[mem_id]["type_4"] if "type_4" in old_db[mem_id] else 0
    #
    #         stmt = insert(spots).values(
    #             member_id=mem_id, legendary=counter_lege_old,
    #             rare=counter_rare_old, common=counter_common_old)
    #         do_update_stmt = stmt.on_duplicate_key_update(legendary=stmt.inserted.legendary + counter_lege,
    #                                                       rare=stmt.inserted.rare + counter_rare,
    #                                                       common=stmt.inserted.common + counter_common)
    #         self.conn.execute(do_update_stmt)
    #
    #         stmt = insert(spots_temp).values(
    #             member_id=mem_id, legendary=counter_lege_old,
    #             rare=counter_rare_old, common=counter_common_old)
    #         do_update_stmt = stmt.on_duplicate_key_update(legendary=stmt.inserted.legendary + counter_lege,
    #                                                       rare=stmt.inserted.rare + counter_rare,
    #                                                       common=stmt.inserted.common + counter_common)
    #         self.conn.execute(do_update_stmt)
    #
    #     await ctx.send(f"Spot tables updated with old data", delete_after=5.0)
    #     dt_string = self.bot.get_current_time()
    #     print(f'({dt_string})\t[{self.__class__.__name__}]: Spot tables updated with old data')
    #     self.conn.close()

    # ----- SPOTTING OPERATIONS -----

    # Update spots tables
    @classmethod
    async def db_count_spot(cls, _id: int, monster_type: str):
        cls.conn = cls.engine.connect()
        cls.db_count_spot_table(spots, _id, monster_type)
        cls.db_count_spot_table(spots_temp, _id, monster_type)
        cls.conn.close()

    @classmethod
    def db_count_spot_table(cls, table, _id: int, monster_type: str):
        stmt = select(table.c.member_id, table.c.legendary, table.c.rare, table.c.common,
                      table.c.event1,
                      table.c.event2).where(
            table.c.member_id == _id)
        result = cls.conn.execute(stmt)
        counter = 0
        for nr_of_kills in result.columns(monster_type, 'legendary'):
            counter = nr_of_kills[0]
        if monster_type == "event1":
            values = cls.db_count_spot_table_event(table, _id, monster_type, counter)
        else:
            values = {f"{monster_type}": counter + 1}
        stmt = update(table).where(table.c.member_id == _id).values(values)
        cls.conn.execute(stmt)

    @classmethod
    def db_count_spot_table_event(cls, table, _id, monster_type: str, counter: int):
        stmt = select(table.c.member_id, table.c.legendary, table.c.rare, table.c.common,
                      table.c.event1,
                      table.c.event2).where(
            table.c.member_id == _id)
        result = cls.conn.execute(stmt)
        counter_leg = 0
        for nr_of_kills_leg in result.columns('legendary'):
            counter_leg = nr_of_kills_leg[0]
        values = {f"{monster_type}": counter + 1, "legendary": counter_leg + 1}
        return values

    # Save coords from spotting channels to database
    @classmethod
    async def db_save_coords(cls, _coords: str, _monster_type):
        cls.conn = cls.engine.connect()
        stmt = insert(coords).values(coords=_coords, monster_type=_monster_type)
        cls.conn.execute(stmt)
        cls.conn.close()

    # Clear data from spots_temp table(for events etc)
    @classmethod
    async def db_clear_spots_temp_table(cls):
        cls.conn = cls.engine.connect()
        stmt = delete(spots_temp)
        cls.conn.execute(stmt)
        cls.conn.close()

    # ----- LEADERBOARD OPERATIONS -----

    # Return all members' spots
    @classmethod
    async def db_get_spots_df(cls):
        cls.conn = cls.engine.connect()
        stmt = select(spots.c.member_id, member.c.display_name, spots.c.legendary, spots.c.rare,
                      spots.c.common, spots.c.event1, spots.c.event2
                      ).select_from(member
                                    ).join(spots, member.c.id == spots.c.member_id)
        cls.conn.execute(stmt)
        df = pd.read_sql(stmt, cls.conn)
        cls.conn.close()
        return df

    # ----- WARN OPERATIONS -----

    # Add member's warn to database
    @classmethod
    async def db_add_warn(cls, _member: int, _reason: str):
        cls.conn = cls.engine.connect()
        stmt = insert(warn).values(member_id=_member, reason=_reason, date=datetime.now())
        cls.conn.execute(stmt)
        cls.conn.close()

    # Get member's warns from database
    @classmethod
    async def db_get_warns(cls, _member: int):
        cls.conn = cls.engine.connect()
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
        cls.conn.close()
        return warns_list, counter

    # Remove all member's warns
    @classmethod
    async def db_remove_warns(cls, _member: int):
        cls.conn = cls.engine.connect()
        stmt = delete(warn).where(warn.c.member_id == _member)
        cls.conn.execute(stmt)
        cls.conn.close()

    # ----- MEMBER OPERATIONS -----

    # Return member's spots
    @classmethod
    async def db_get_member_stats(cls, _member: int):
        cls.conn = cls.engine.connect()
        stmt = select(member.c.display_name, spots.c.legendary, spots.c.rare, spots.c.common).select_from(member).join(
            spots,
            member.c.id == spots.c.member_id).where(spots.c.member_id == _member)
        df = pd.read_sql(stmt, cls.conn)
        cls.conn.close()
        return df

    # ----- COORDS OPERATIONS -----

    # Return coords
    @classmethod
    async def db_get_coords(cls):
        cls.conn = cls.engine.connect()
        stmt = select(coords.c.id, coords.c.coords, coords.c.monster_type).select_from(coords)
        df = pd.read_sql(stmt, cls.conn)
        cls.conn.close()
        return df


def setup(bot: commands.Bot):
    bot.add_cog(DatabaseCog(bot))
