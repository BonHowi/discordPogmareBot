import os

import discord
from discord.ext import commands, tasks
from discord_slash import cog_ext, SlashContext

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

    def cog_unload(self):
        self.db_update_loop.cancel()

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
        self.create_log_msg(f"Refreshing member and spots tables")
        for guild_member in guild.members:
            # Member tables
            self.db_add_update_member(guild_member)
            # Spots tables
            self.db_add_update_spots(spots, guild_member)
            self.db_add_update_spots(spots_temp, guild_member)
        self.create_log_msg(f"Member and spots tables refreshed")
        self.conn.close()

    @tasks.loop(hours=12)
    async def db_update_loop(self):
        await self.db_update()
        await self.db_backup_database()

    @db_update_loop.before_loop
    async def before_db_update_loop(self):
        self.create_log_msg(f"Waiting until Bot is ready")
        await self.bot.wait_until_ready()

    # Add member to database on member join
    @commands.Cog.listener()
    async def on_member_join(self, _member):
        self.db_add_update_member(_member)
        self.db_add_update_spots(spots, _member)
        self.db_add_update_spots(spots_temp, _member)

    # Backup database
    async def db_backup_database(self):
        now = datetime.now()
        cmd = f"mysqldump -u {get_settings('DB_U')} " \
              f"--result-file=database_backup/backup-{now.strftime('%m-%d-%Y')}.sql " \
              f"-p{get_settings('DB_P')} server_database"
        os.system(cmd)
        self.create_log_msg(f"Database backed up")

    # ----- SPOTTING OPERATIONS -----

    # Update spots tables
    @classmethod
    async def db_count_spot(cls, _id: int, monster_type: str):
        cls.conn = cls.engine.connect()
        cls.db_count_spot_table(spots, _id, monster_type)
        cls.db_count_spot_table(spots_temp, _id, monster_type)
        cls.conn.close()

    # TODO: make rares in events possible
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

    @cog_ext.cog_slash(name="changeMemberSpots", guild_ids=cogbase.GUILD_IDS,
                       description="Change member spotting stats",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_MODS)
    async def change_member_spots(self, ctx: SlashContext, user: discord.Member, spot_type: str, number: int):
        self.conn = self.engine.connect()
        stmt = f"""UPDATE server_database.spots SET {spot_type} = {number} """ \
               f"""WHERE (member_id = {user.id});"""
        self.conn.execute(stmt)
        await ctx.send(f"{user.display_name} spots changed", hidden=True)
        self.conn.close()

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
