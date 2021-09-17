import json
import math
import os
from datetime import datetime
import time
import discord
import psutil
from discord.utils import get
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
                       permissions=cogbase.PERMISSION_ADMINS)
    async def clear_temp_spots_table(self, ctx):
        await DatabaseCog.db_clear_spots_temp_table()
        await ctx.send(f"Temp spots table was cleared", hidden=True)
        await self.reload_cog(ctx, "cogs.databasecog")

    # Reloads cog, very useful because there is no need to exit the bot after updating cog
    async def reload_cog(self, ctx: SlashContext, module: str):
        """Reloads a module."""
        dt_string = self.bot.get_current_time()
        try:
            self.bot.load_extension(f"{module}")
            await ctx.send(f'[{module}] loaded', hidden=True)
            print(f'({dt_string})\t[{self.__class__.__name__}]: {module} loaded')
        except commands.ExtensionAlreadyLoaded:
            self.bot.unload_extension(module)
            self.bot.load_extension(module)
            await ctx.send(f'[{module}] reloaded', hidden=True)
            print(f'({dt_string})\t[{self.__class__.__name__}]: {module} reloaded')
        except commands.ExtensionNotFound:
            await ctx.send(f'[{module}] not found', hidden=True)
            print(f'({dt_string})\t[{self.__class__.__name__}]: {module} not found')

    # Command for reloading specific cog
    @cog_ext.cog_slash(name="reloadCog", guild_ids=cogbase.GUILD_IDS,
                       description="Reload cog",
                       permissions=cogbase.PERMISSION_ADMINS)
    async def reload_cog_command(self, ctx: SlashContext, module: str):
        await self.reload_cog(ctx, module)

    # Command for reloading all cogs
    @cog_ext.cog_slash(name="reloadAllCogs", guild_ids=cogbase.GUILD_IDS,
                       description="Reload cog",
                       permissions=cogbase.PERMISSION_ADMINS)
    async def reload_all_cogs(self, ctx: SlashContext = None):
        for cog in list(self.bot.extensions.keys()):
            await self.reload_cog(ctx, cog)
        await ctx.send(f'All cogs reloaded', hidden=True)

    @cog_ext.cog_slash(name="saveCoordinates", guild_ids=cogbase.GUILD_IDS,
                       description="Get your spot stats",
                       permissions=cogbase.PERMISSION_ADMINS)
    async def save_coordinates(self, ctx: SlashContext):
        coords_df = await DatabaseCog.db_get_coords()
        coords_df[['latitude', 'longitude']] = coords_df['coords'].str.split(',', expand=True)
        coords_df.to_excel(r'server_files/coords.xlsx', index=False)
        await ctx.send(f"Coords saved", hidden=True)
        dt_string = self.bot.get_current_time()
        print(f'({dt_string})\t[{self.__class__.__name__}]: Coords saved to server_files/coords.xlsx')

    # Get member info
    @cog_ext.cog_slash(name="memberinfo", guild_ids=cogbase.GUILD_IDS,
                       description="Get member info",
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
                       permissions=cogbase.PERMISSION_MODS)
    async def system(self, ctx):
        """Get status of the system."""
        process_uptime = time.time() - self.bot.start_time
        process_uptime = time.strftime("%ed %Hh %Mm %Ss", time.gmtime(process_uptime))
        system_uptime = time.time() - psutil.boot_time()
        system_uptime = time.strftime("%ed %Hh %Mm %Ss", time.gmtime(system_uptime))
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


def setup(bot: commands.Bot):
    bot.add_cog(UtilsCog(bot))
