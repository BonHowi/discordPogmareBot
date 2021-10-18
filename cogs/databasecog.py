import os
from datetime import datetime

import discord
import pandas as pd
from discord.ext import commands, tasks
from discord_slash import cog_ext, SlashContext
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, ForeignKey, \
    BigInteger, update, select, DateTime, delete
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.sql import func

import cogs.cogbase as cogbase
from modules.get_settings import get_settings

metadata_obj = MetaData()

member = Table('member', metadata_obj,
               Column('id', BigInteger, primary_key=True),
               Column('name', String(50), nullable=False),
               Column('display_name', String(50), nullable=False)
               )
fk_member_id = "member.id"

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

spots_lege = Table('spots_lege', metadata_obj,
                   Column('member_id', BigInteger, ForeignKey(fk_member_id), primary_key=True),
                   Column('AncientLeshen', Integer, default=0),
                   Column('Archgriffin', Integer, default=0),
                   Column('CopperWyvern', Integer, default=0),
                   Column('D\'jinni', Integer, default=0),
                   Column('DungShaelmaar', Integer, default=0),
                   Column('Erynia', Integer, default=0),
                   Column('Frightener', Integer, default=0),
                   Column('GraphiteSlyzard', Integer, default=0),
                   Column('GrimHag', Integer, default=0),
                   Column('Hym', Integer, default=0),
                   Column('IceElemental', Integer, default=0),
                   Column('IceGiant', Integer, default=0),
                   Column('IceTroll', Integer, default=0),
                   Column('Katakan', Integer, default=0),
                   Column('MottledGarkain', Integer, default=0),
                   Column('Penitent', Integer, default=0),
                   Column('PlagueMaiden', Integer, default=0),
                   Column('Sandcrab', Integer, default=0),
                   Column('SilverBasilisk', Integer, default=0),
                   Column('SwampHag', Integer, default=0),
                   Column('TarryChort', Integer, default=0),
                   Column('Tormented', Integer, default=0),
                   Column('Ulfhedinn', Integer, default=0),
                   Column('UnseenElder', Integer, default=0),
                   Column('WaterDevil', Integer, default=0),
                   Column('WhiteStriga', Integer, default=0)
                   )

spots_rare = Table('spots_rare', metadata_obj,
                   Column('member_id', BigInteger, ForeignKey(fk_member_id), primary_key=True),
                   Column('Beann\'Shie', Integer, default=0),
                   Column('BlueForktail', Integer, default=0),
                   Column('Bruxa', Integer, default=0),
                   Column('Burier', Integer, default=0),
                   Column('Cockatrice', Integer, default=0),
                   Column('DepthLurker', Integer, default=0),
                   Column('Devourer', Integer, default=0),
                   Column('DrownedDead', Integer, default=0),
                   Column('EndregaCharger', Integer, default=0),
                   Column('EndregaWarrior', Integer, default=0),
                   Column('Farbaut', Integer, default=0),
                   Column('FireElemental', Integer, default=0),
                   Column('GarkainAlpha', Integer, default=0),
                   Column('Gernichora', Integer, default=0),
                   Column('GraySlyzard', Integer, default=0),
                   Column('GreenHarpy', Integer, default=0),
                   Column('Grimnir', Integer, default=0),
                   Column('Grottore', Integer, default=0),
                   Column('Howler', Integer, default=0),
                   Column('IgnisFatuus', Integer, default=0),
                   Column('KikimoreWarrior', Integer, default=0),
                   Column('Leshen', Integer, default=0),
                   Column('LeshenHound', Integer, default=0),
                   Column('Liho', Integer, default=0),
                   Column('Lycanthrope', Integer, default=0),
                   Column('MagmaTroll', Integer, default=0),
                   Column('NekkerShaman', Integer, default=0),
                   Column('Nightmare', Integer, default=0),
                   Column('NightSuccubus', Integer, default=0),
                   Column('Putrifier', Integer, default=0),
                   Column('RoyalFoglet', Integer, default=0),
                   Column('RoyalNekker', Integer, default=0),
                   Column('RoyalWyvern', Integer, default=0),
                   Column('RussetShaelmaar', Integer, default=0),
                   Column('Scurver', Integer, default=0),
                   Column('Shrieker', Integer, default=0),
                   Column('SpottedAlghoul', Integer, default=0),
                   Column('StoneGolem', Integer, default=0),
                   Column('Striga', Integer, default=0),
                   Column('SylvanDearg', Integer, default=0),
                   Column('Wailwraith', Integer, default=0)
                   )


class DatabaseCog(cogbase.BaseCog):
    user = get_settings("DB_U")
    password = get_settings("DB_P")
    conn_string = f"mysql+mysqldb://{user}:{password}@localhost/server_database?charset=utf8mb4"
    engine = create_engine(conn_string, pool_recycle=3600)
    metadata_obj.create_all(engine)
    conn = None

    def __init__(self, base):
        super().__init__(base)

        # Connect to database
        self.engine = DatabaseCog.engine
        metadata_obj.create_all(self.engine)
        self.db_update_loop.start()
        self.conn = DatabaseCog.conn

    def cog_unload(self) -> None:
        self.db_update_loop.cancel()

    # ----- BASE DATABASE OPERATIONS -----

    # Add or update member in member table
    def db_add_update_member(self, guild_member) -> None:
        self.conn = self.engine.connect()
        stmt = insert(member).values(
            id=guild_member.id, name=guild_member.name,
            display_name=guild_member.display_name)
        do_update_stmt = stmt.on_duplicate_key_update(
            name=stmt.inserted.name, display_name=stmt.inserted.display_name
        )
        self.conn.execute(do_update_stmt)
        self.conn.close()

    # Add or update spots in spots table
    def db_add_update_spots(self, spots_table, guild_member) -> None:
        self.conn = self.engine.connect()
        stmt = insert(spots_table).values(
            member_id=guild_member.id)
        do_update_stmt = stmt.on_duplicate_key_update(member_id=stmt.inserted.member_id)
        self.conn.execute(do_update_stmt)
        self.conn.close()

    # Add or refresh all guild members and spots to database
    async def db_update(self) -> None:
        self.conn = self.engine.connect()
        guild = self.bot.get_guild(self.bot.guild[0])
        self.create_log_msg("Refreshing member and spots tables")
        for guild_member in guild.members:
            # Member tables
            self.db_add_update_member(guild_member)
            # Spots tables
            self.db_add_update_spots(spots, guild_member)
            self.db_add_update_spots(spots_temp, guild_member)
            self.db_add_update_spots(spots_lege, guild_member)
            self.db_add_update_spots(spots_rare, guild_member)
        self.create_log_msg("Member and spots tables refreshed")
        self.conn.close()

    @tasks.loop(hours=12)
    async def db_update_loop(self) -> None:
        await self.db_update()
        await self.db_backup_database()

    @db_update_loop.before_loop
    async def before_db_update_loop(self) -> None:
        self.create_log_msg("Waiting until Bot is ready")
        await self.bot.wait_until_ready()

    # Add member to database on member join
    @commands.Cog.listener()
    async def on_member_join(self, guild_member) -> None:
        self.db_add_update_member(guild_member)
        self.db_add_update_spots(spots, guild_member)
        self.db_add_update_spots(spots_temp, guild_member)
        self.db_add_update_spots(spots_lege, guild_member)
        self.db_add_update_spots(spots_rare, guild_member)

    # Backup database
    async def db_backup_database(self) -> None:
        now = datetime.now()
        cmd = f"mysqldump -u {get_settings('DB_U')} " \
              f"--result-file=database_backup/backup-{now.strftime('%m-%d-%Y')}.sql " \
              f"-p{get_settings('DB_P')} server_database"
        os.system(cmd)
        self.create_log_msg("Database backed up")

    # ----- SPOTTING OPERATIONS -----

    # Update spots tables
    @classmethod
    async def db_count_spot(cls, _id: int, monster_type: str, monster_name: str) -> None:
        cls.conn = cls.engine.connect()
        cls.db_count_spot_table(spots, _id, monster_type, monster_name, False)
        cls.db_count_spot_table(spots_temp, _id, monster_type, monster_name, True)
        cls.conn.close()

    @classmethod
    def db_count_spot_table(cls, table, _id: int, monster_type: str, monster_name: str,
                            temp_table: bool = True) -> None:
        cls.conn = cls.engine.connect()
        stmt = select(table.c.member_id, table.c.legendary, table.c.rare, table.c.common,
                      table.c.event1,
                      table.c.event2).where(
            table.c.member_id == _id)
        result = cls.conn.execute(stmt)
        cls.conn.close()
        counter = 0
        for nr_of_kills in result.columns(monster_type, 'legendary'):
            counter = nr_of_kills[0]
        if monster_type == "event1":
            values = cls.db_count_spot_table_event(table, _id, monster_type, counter)
        else:
            values = {f"{monster_type}": counter + 1}
        stmt = update(table).where(table.c.member_id == _id).values(values)
        cls.conn = cls.engine.connect()
        cls.conn.execute(stmt)
        cls.conn.close()
        if not temp_table:
            cls.db_count_monster_spot(_id, monster_type, monster_name)

    @classmethod
    def db_count_monster_spot(cls, _id: int, monster_type: str, monster_name: str) -> None:
        bot_id = 881167775635234877
        if monster_type == "legendary":
            values_lege_member = cls.db_count_spot_table_monster(spots_lege, _id, monster_name)
            stmt = update(spots_lege).where(spots_lege.c.member_id == _id).values(values_lege_member)
            cls.conn = cls.engine.connect()
            cls.conn.execute(stmt)
            cls.conn.close()
            values_lege_total = cls.db_count_spot_table_monster(spots_lege, bot_id, monster_name)
            stmt = update(spots_lege).where(spots_lege.c.member_id == bot_id).values(values_lege_total)
            cls.conn = cls.engine.connect()
            cls.conn.execute(stmt)
            cls.conn.close()
        elif monster_type == "rare":
            values_rare_member = cls.db_count_spot_table_monster(spots_rare, _id, monster_name)
            stmt = update(spots_rare).where(spots_rare.c.member_id == _id).values(values_rare_member)
            cls.conn = cls.engine.connect()
            cls.conn.execute(stmt)
            cls.conn.close()
            values_rare_total = cls.db_count_spot_table_monster(spots_rare, bot_id, monster_name)
            stmt = update(spots_rare).where(spots_rare.c.member_id == bot_id).values(values_rare_total)
            cls.conn = cls.engine.connect()
            cls.conn.execute(stmt)
            cls.conn.close()

    @classmethod
    def db_count_spot_table_event(cls, table, _id, monster_type: str, counter: int) -> dict:
        cls.conn = cls.engine.connect()
        stmt = select(table.c.member_id, table.c.legendary, table.c.rare, table.c.common,
                      table.c.event1,
                      table.c.event2).where(
            table.c.member_id == _id)
        result = cls.conn.execute(stmt)
        counter_leg = 0
        for nr_of_kills_leg in result.columns('legendary'):
            counter_leg = nr_of_kills_leg[0]
        values = {f"{monster_type}": counter + 1, "legendary": counter_leg + 1}
        cls.conn.close()
        return values

    @classmethod
    def db_count_spot_table_monster(cls, table, guild_member_id: int, monster_name: str) -> dict:
        cls.conn = cls.engine.connect()
        stmt = select(table).where(table.c.member_id == guild_member_id)
        result = cls.conn.execute(stmt)
        counter = 0
        for nr_of_kills_leg in result.columns(f"{monster_name}"):
            counter = nr_of_kills_leg[0]
        values = {f"{monster_name}": counter + 1}
        cls.conn.close()
        return values

    # Save coords from spotting channels to database
    @classmethod
    async def db_save_coords(cls, coord: str, monster_type: str) -> None:
        cls.conn = cls.engine.connect()
        stmt = insert(coords).values(coords=coord, monster_type=monster_type)
        cls.conn.execute(stmt)
        cls.conn.close()

    # Clear data from spots_temp table(for events etc)
    @classmethod
    async def db_clear_spots_temp_table(cls) -> None:
        cls.conn = cls.engine.connect()
        stmt = delete(spots_temp)
        cls.conn.execute(stmt)
        cls.conn.close()

    # ----- LEADERBOARD OPERATIONS -----

    # Return total spotting stats
    @classmethod
    async def db_get_total_spots_df(cls, member_id: int, leaderboard_type: int) -> pd.DataFrame:
        df = pd.DataFrame
        cls.conn = cls.engine.connect()
        if leaderboard_type == 1:
            stmt = select(spots_lege)
            df = pd.read_sql(stmt, cls.conn)
        elif leaderboard_type == 0:
            stmt = select(spots_rare)
            df = pd.read_sql(stmt, cls.conn)
        df = df.loc[df['member_id'] == member_id]
        cls.conn.close()
        return df

    # Return all members' spots
    @classmethod
    async def db_get_spots_df(cls) -> pd.DataFrame:
        cls.conn = cls.engine.connect()
        stmt = select(spots.c.member_id, member.c.display_name, spots.c.legendary, spots.c.rare,
                      spots.c.common, spots.c.event1, spots.c.event2
                      ).select_from(member
                                    ).join(spots, member.c.id == spots.c.member_id)
        cls.conn.execute(stmt)
        df = pd.read_sql(stmt, cls.conn)
        cls.conn.close()
        return df

    @classmethod
    async def db_get_common_sum(cls) -> int:
        cls.conn = cls.engine.connect()
        stmt = select(func.sum(spots.c.common).label("sum"))
        result = cls.conn.execute(stmt)
        sum_common = 0
        for nr_of_kills_leg in result.columns("sum"):
            sum_common = nr_of_kills_leg[0]
        cls.conn.close()
        return sum_common

    @classmethod
    async def db_get_monster_spots_df(cls) -> pd.DataFrame:
        # TODO: Why does tables join not work?
        cls.conn = cls.engine.connect()
        stmt = select(spots_lege)
        cls.conn.execute(stmt)
        df_lege = pd.read_sql(stmt, cls.conn)
        cls.conn.close()
        cls.conn = cls.engine.connect()
        stmt = select(spots_rare)
        cls.conn.execute(stmt)
        df_rare = pd.read_sql(stmt, cls.conn)
        cls.conn.close()
        return pd.merge(df_lege, df_rare, on=["member_id"])

    @classmethod
    async def db_get_member_names(cls) -> pd.DataFrame:
        cls.conn = cls.engine.connect()
        stmt = select(member.c.id.label("member_id"), member.c.display_name)
        cls.conn.execute(stmt)
        df_member_names = pd.read_sql(stmt, cls.conn)
        cls.conn.close()
        return df_member_names

    # ----- WARN OPERATIONS -----

    # Add member's warn to database
    @classmethod
    async def db_add_warn(cls, guild_member_id: int, reason: str) -> None:
        cls.conn = cls.engine.connect()
        stmt = insert(warn).values(member_id=guild_member_id, reason=reason, date=datetime.now())
        cls.conn.execute(stmt)
        cls.conn.close()

    # Get member's warns from database
    @classmethod
    async def db_get_warns(cls, guild_member_id: int) -> tuple:
        cls.conn = cls.engine.connect()
        stmt = select(warn.c.reason, warn.c.date).select_from(member).join(warn, member.c.id == warn.c.member_id).where(
            member.c.id == guild_member_id)
        result = cls.conn.execute(stmt)
        date_warn = []
        counter = 0
        for warns in result.columns("reason", "date"):
            reason_with_date = [warns[1], warns[0]]
            date_warn.append(reason_with_date)
            counter += 1
        warns_list = [': \t'.join(str(elem) for elem in sublist) for sublist in date_warn]

        cls.conn.close()
        return warns_list, counter

    # Remove all member's warns
    @classmethod
    async def db_remove_warns(cls, guild_member: int) -> None:
        cls.conn = cls.engine.connect()
        stmt = delete(warn).where(warn.c.member_id == guild_member)
        cls.conn.execute(stmt)
        cls.conn.close()

    # ----- MEMBER OPERATIONS -----

    # Return member's spots
    @classmethod
    async def db_get_member_stats(cls, guild_member: int) -> pd.DataFrame:
        cls.conn = cls.engine.connect()
        stmt = select(spots.c.member_id, member.c.display_name, spots.c.legendary, spots.c.rare, spots.c.common
                      ).select_from(member).join(spots,
                                                 member.c.id == spots.c.member_id)\
            .where(spots.c.member_id == guild_member)
        df = pd.read_sql(stmt, cls.conn)
        cls.conn.close()
        return df

    @classmethod
    async def db_get_member_monsters(cls, guild_member: int) -> pd.DataFrame:
        cls.conn = cls.engine.connect()
        stmt = select(spots_lege).where(spots_lege.c.member_id == guild_member)
        cls.conn.execute(stmt)
        df_lege = pd.read_sql(stmt, cls.conn)
        cls.conn.close()
        cls.conn = cls.engine.connect()
        stmt = select(spots_rare).where(spots_rare.c.member_id == guild_member)
        cls.conn.execute(stmt)
        df_rare = pd.read_sql(stmt, cls.conn)
        cls.conn.close()
        return pd.merge(df_lege, df_rare, on=["member_id"])

    @cog_ext.cog_slash(name="changeMemberSpots", guild_ids=cogbase.GUILD_IDS,
                       description="Change member spotting stats",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_ADMINS)
    async def change_member_spots(self, ctx: SlashContext, user: discord.Member, spot_type: str, number: int) -> None:
        self.conn = self.engine.connect()
        stmt = f"""UPDATE server_database.spots SET {spot_type} = {number} """ \
               f"""WHERE (member_id = {user.id});"""
        self.conn.execute(stmt)
        await ctx.send(f"{user.display_name} spots changed", hidden=True)
        self.conn.close()

    # ----- COORDS OPERATIONS -----

    # Return coords
    @classmethod
    async def db_get_coords(cls) -> pd.DataFrame:
        cls.conn = cls.engine.connect()
        stmt = select(coords.c.id, coords.c.coords, coords.c.monster_type).select_from(coords)
        df = pd.read_sql(stmt, cls.conn)
        cls.conn.close()
        return df


def setup(bot: commands.Bot) -> None:
    bot.add_cog(DatabaseCog(bot))
