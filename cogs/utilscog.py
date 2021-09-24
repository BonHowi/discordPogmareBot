import json
import math
import os
import re
from datetime import datetime
import time
import discord
import psutil
from discord.utils import get
from numpyencoder import NumpyEncoder

from modules.get_settings import get_settings
import cogs.cogbase as cogbase
from discord.ext import commands
from discord_slash import cog_ext, SlashContext
from cogs.databasecog import DatabaseCog
from modules.pull_config.pull_config import get_config


class UtilsCog(cogbase.BaseCog):
    def __init__(self, base):
        super().__init__(base)

    # OTHER
    # Pull config.json from Google Sheets
    @cog_ext.cog_slash(name="pullConfig", guild_ids=cogbase.GUILD_IDS,
                       description="Pull config from google sheets",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_ADMINS)
    async def pull_config(self, ctx: SlashContext):
        get_config()
        with open('server_files/config.json', 'r', encoding='utf-8-sig') as fp:
            self.bot.config = json.load(fp)
            await self.create_roles(ctx, True)
            await self.create_roles(ctx, False)
            dt_string = self.bot.get_current_time()
            print(f"({dt_string})\t[{self.__class__.__name__}]: Finished data pull")
        await ctx.send(f"Config.json updated", hidden=True)

    # Create roles if pull_config gets non existent roles
    async def create_roles(self, ctx: SlashContext, common: bool):
        milestones = "common_milestones" if common else "total_milestones"
        for mon_type in self.bot.config[milestones][0]:
            if get(ctx.guild.roles, name=mon_type):
                continue
            else:
                await ctx.guild.create_role(name=mon_type)
                dt_string = self.bot.get_current_time()
                print(f"({dt_string})\t[{self.__class__.__name__}]: {mon_type} role created")

    # Clear temp spots table in database
    @cog_ext.cog_slash(name="clearTempSpots", guild_ids=cogbase.GUILD_IDS,
                       description="Clear temp spots table in database",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_ADMINS)
    async def clear_temp_spots_table(self, ctx):
        await DatabaseCog.db_clear_spots_temp_table()
        await ctx.send(f"Temp spots table was cleared", hidden=True)
        await self.reload_cog(ctx, "databasecog")

    # Reloads cog, very useful because there is no need to exit the bot after updating cog
    async def reload_cog(self, ctx: SlashContext, module: str):
        """Reloads a module."""
        module = f"cogs.{module}"
        dt_string = self.bot.get_current_time()
        try:
            self.bot.load_extension(f"{module}")
            await ctx.send(f'[{module}] loaded', delete_after=4.0)
            print(f'({dt_string})\t[{self.__class__.__name__}]: {module} loaded')
        except commands.ExtensionAlreadyLoaded:
            self.bot.unload_extension(module)
            self.bot.load_extension(module)
            await ctx.send(f'[{module}] reloaded', delete_after=4.0)
            print(f'({dt_string})\t[{self.__class__.__name__}]: {module} reloaded')
        except commands.ExtensionNotFound:
            await ctx.send(f'[{module}] not found', delete_after=4.0)
            print(f'({dt_string})\t[{self.__class__.__name__}]: {module} not found')

    # Command for reloading specific cog
    @cog_ext.cog_slash(name="reloadCog", guild_ids=cogbase.GUILD_IDS,
                       description="Reload cog",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_ADMINS)
    async def reload_cog_command(self, ctx: SlashContext, module: str):
        await self.reload_cog(ctx, module)

    # Command for reloading all cogs
    @cog_ext.cog_slash(name="reloadAllCogs", guild_ids=cogbase.GUILD_IDS,
                       description="Reload cog",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_ADMINS)
    async def reload_all_cogs(self, ctx: SlashContext = None):
        for cog in list(self.bot.extensions.keys()):
            cog = cog.replace('cogs.', '')
            await self.reload_cog(ctx, cog)
        await ctx.send(f'All cogs reloaded', delete_after=5.0)

    @cog_ext.cog_slash(name="saveCoordinates", guild_ids=cogbase.GUILD_IDS,
                       description="Get your spot stats",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_ADMINS)
    async def save_coordinates(self, ctx: SlashContext):
        coords_df = await DatabaseCog.db_get_coords()
        coords_df = coords_df[coords_df.coords.str.contains(",")]
        print(coords_df)
        coords_df[['latitude', 'longitude']] = coords_df['coords'].str.split(',', 1, expand=True)
        coords_df.to_excel(r'server_files/coords.xlsx', index=False)
        await ctx.send(f"Coords saved", hidden=True)
        dt_string = self.bot.get_current_time()
        print(f'({dt_string})\t[{self.__class__.__name__}]: Coords saved to server_files/coords.xlsx')

    # Get member info
    @cog_ext.cog_slash(name="memberinfo", guild_ids=cogbase.GUILD_IDS,
                       description="Get member info",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_ADMINS)
    async def memberinfo(self, ctx: SlashContext, *, user: discord.Member = None):
        if user is None:
            user = ctx.author
        date_format = "%a, %d %b %Y %I:%M %p"
        embed = discord.Embed(color=0xFF0000, description=user.mention)
        embed.set_author(name=str(user), icon_url=user.avatar_url)
        embed.set_thumbnail(url=user.avatar_url)
        embed.add_field(name="Joined Server", value=user.joined_at.strftime(date_format), inline=False)
        members = sorted(ctx.guild.members, key=lambda m: m.joined_at)
        embed.add_field(name="Join Position", value=str(members.index(user) + 1), inline=False)
        embed.add_field(name="Joined Discord", value=user.created_at.strftime(date_format), inline=False)
        if len(user.roles) > 1:
            role_string = ' '.join([r.mention for r in user.roles][1:])
            embed.add_field(name="Roles [{}]".format(len(user.roles) - 1), value=role_string, inline=False)
        embed.set_footer(text='ID: ' + str(user.id))
        return await ctx.send(embed=embed)

    # Backup database to a file
    @cog_ext.cog_slash(name="backupDatabase", guild_ids=cogbase.GUILD_IDS,
                       description="Backup database to a file",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_MODS)
    async def backup_database(self, ctx: SlashContext):
        now = datetime.now()
        cmd = f"mysqldump -u {get_settings('DB_U')} " \
              f"--result-file=database_backup/backup-{now.strftime('%m-%d-%Y')}.sql " \
              f"-p{get_settings('DB_P')} server_database"
        os.system(cmd)
        await ctx.send(f"Database backed up", hidden=True)

    # System stats
    @cog_ext.cog_slash(name="systemStatus", guild_ids=cogbase.GUILD_IDS,
                       description="Get status of the system",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_MODS)
    async def system(self, ctx):
        """Get status of the system."""
        process_uptime = time.time() - self.bot.start_time
        process_uptime = time.strftime("%ed %Hh %Mm %Ss", time.gmtime(process_uptime))
        process_uptime = process_uptime.replace(re.search(r'\d+', process_uptime).group(),
                                                str(int(re.search(r'\d+', process_uptime).group()) - 1), 1)
        system_uptime = time.time() - psutil.boot_time()
        system_uptime = time.strftime("%ed %Hh %Mm %Ss", time.gmtime(system_uptime))
        system_uptime = system_uptime.replace(re.search(r'\d+', system_uptime).group(),
                                              str(int(re.search(r'\d+', system_uptime).group()) - 1), 1)
        mem = psutil.virtual_memory()
        pid = os.getpid()
        memory_use = psutil.Process(pid).memory_info()[0]

        data = [
            ("Version", self.bot.version),
            ("Process uptime", process_uptime),
            ("Process memory", f"{memory_use / math.pow(1024, 2):.2f}MB"),
            ("System uptime", system_uptime),
            ("CPU Usage", f"{psutil.cpu_percent()}%"),
            ("RAM Usage", f"{mem.percent}%"),
        ]

        content = discord.Embed(
            title=":computer: System status",
            colour=int("5dadec", 16),
            description="\n".join(f"**{x[0]}** {x[1]}" for x in data),
        )
        await ctx.send(embed=content)

    # Change monster type(for events)
    @cog_ext.cog_slash(name="changeMonsterType", guild_ids=cogbase.GUILD_IDS,
                       description="Get status of the system",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_ADMINS)
    async def change_monster_type(self, ctx, monster: str, new_type: int):
        config = self.bot.config
        for mon in config["commands"]:
            if mon["name"] == monster:
                mon["type"] = new_type
                dt_string = self.bot.get_current_time()
                print(f"({dt_string})\t[{get_config.__name__}]: changed type for {monster}")
                await ctx.send(f"{monster}'s type changed", hidden=True)
                break

        self.bot.config = config
        with open('server_files/config.json', 'w', encoding='utf8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False, sort_keys=False, cls=NumpyEncoder)

    # Update guides channel
    @cog_ext.cog_slash(name="updateGuides", guild_ids=cogbase.GUILD_IDS,
                       description=" ",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_MODS)
    async def change_monster_type(self, ctx: SlashContext):
        embed = discord.Embed(title="SPOOFING GUIDES", color=0x878a00)
        embed.add_field(name="Recommended Fake GPS App for Android users",
                        value="https://play.google.com/store/apps/details?id=com.theappninjas.fakegpsjoystick",
                        inline=True)
        embed.add_field(name="Recommended Fake GPS App for iOS users",
                        value="https://www.thinkskysoft.com/itools", inline=False)
        embed.add_field(name="Recommended android emulator for Windows and Mac",
                        value="https://www.bignox.com", inline=False)
        embed.add_field(name="YT Guide for Fake GPS Location recommended app (by @ChampattioNonNightMareMare)",
                        value="https://www.youtube.com/watch?v=wU7qOLEm7qQ", inline=False)
        embed.add_field(
            name="Nox guide for creating macro and keyboard mapping; "
                 "it can help in automatically making potion, fight, blocks signs etc.",
            value="https://support.bignox.com/en/keyboard/macro1", inline=False)
        await ctx.send(embed=embed)

        embed = discord.Embed(title="GAME GUIDES", color=0x8a3c00)
        embed.add_field(name="Advanced Combat guide", value="https://www.youtube.com/watch?v=-D0wIzwxp0Y",
                        inline=False)
        embed.add_field(name="Guide to the game quests",
                        value="https://docs.google.com/document/d/"
                              "1vK1HfJlglTluNdypzH3XbQDi0vgJ0SNi2lUHbk3lqcE/edit",
                        inline=False)
        embed.add_field(name="Recommended Skill Tree (by @Sagar)",
                        value="https://pasteboard.co/LYjVo2u1aIDt.jpg%", inline=False)
        await ctx.send(embed=embed)

        embed = discord.Embed(title="USEFUL TOOLS", color=0x019827)
        embed.add_field(name="Great sheet for checking monster spawn conditions(credit to @TaraxGoat))",
                        value="https://docs.google.com/spreadsheets/d/"
                              "148qPGW9oYOaYAzpk_a06u2FBnw9rZzAmBZ6AxWFrryI/edit#gid=2093943306",
                        inline=False)
        embed.add_field(name="Website for checking timezones/current time",
                        value="https://www.timeanddate.com/worldclock/?sort=2", inline=False)
        await ctx.send(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(UtilsCog(bot))
