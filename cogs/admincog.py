import asyncio
import discord
import cogs.cogbase as cogbase
from discord.ext import commands
from discord_slash import cog_ext, SlashContext
from cogs.databasecog import DatabaseCog


class AdminCog(cogbase.BaseCog):
    def __init__(self, base):
        super().__init__(base)

    # GENERAL FUNCTIONS
    # Check latency
    @cog_ext.cog_slash(name="ping", guild_ids=cogbase.GUILD_IDS,
                       description="Function for checking latency",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_MODS)
    async def _ping(self, ctx: SlashContext):
        await ctx.send(f"Pong! {round(self.bot.latency * 1000)}ms", delete_after=4.0)

    # Clear messages
    @cog_ext.cog_slash(name="clear", guild_ids=cogbase.GUILD_IDS,
                       description="Function for clearing messages on channel",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_MODS)
    async def _purge(self, ctx: SlashContext, number=1):
        num_messages = int(number)
        await ctx.send(f"Clearing {num_messages} messages!", delete_after=4.0)
        await ctx.channel.purge(limit=num_messages)

    # Disconnect Bot
    @cog_ext.cog_slash(name="exit", guild_ids=cogbase.GUILD_IDS,
                       description="Turn off the bot",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_ADMINS)
    async def _exit(self, ctx: SlashContext):
        await ctx.send(f"Closing Bot", delete_after=1.0)
        dt_string = self.bot.get_current_time()
        print(f"({dt_string})\t[{self.__class__.__name__}]: Exiting Bot")
        await asyncio.sleep(3)
        await self.bot.close()

    # WARN FUNCTIONS

    # Warn user
    @cog_ext.cog_slash(name="warn", guild_ids=cogbase.GUILD_IDS,
                       description="Function for warning users",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_MODS)
    async def _warn(self, ctx: SlashContext, user: discord.User, reason: str):

        await DatabaseCog.db_add_warn(user.id, reason)
        await ctx.send(
            f"{user.mention} was warned for:\n*\"{reason}\"*\n")  # f"Number of warns: {len(current_user['reasons'])}")

    # Get list of user's warns
    @cog_ext.cog_slash(name="warns", guild_ids=cogbase.GUILD_IDS,
                       description="Function for warning users",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_MODS)
    async def _warns(self, ctx: SlashContext, user: discord.User):
        warns, nr_of_warns = await DatabaseCog.db_get_warns(user.id)
        nl = "\n"
        message = f"**{user.name}** has been warned **{nr_of_warns}** times\n\n_Reasons_:\n" \
                  f"{nl.join(warns)}\n"
        await ctx.author.send(message)
        await ctx.send(f"{user.name} warns has been sent to DM", hidden=True)

    # Remove all member's warns
    @cog_ext.cog_slash(name="removeWarns", guild_ids=cogbase.GUILD_IDS,
                       description="Function for removing user's all warns",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_ADMINS)
    async def remove_warns(self, ctx: SlashContext, user: discord.User):
        await DatabaseCog.db_remove_warns(user.id)
        await ctx.send(f"{user.display_name}'s warns were deleted", hidden=True)

    # Mute member
    @cog_ext.cog_slash(name="mute", guild_ids=cogbase.GUILD_IDS,
                       description="Mute member for x minutes",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_MODS)
    async def _mute(self, ctx: SlashContext, user: discord.User, mute_time: int, reason: str):
        duration = mute_time * 60
        guild = ctx.guild
        muted = discord.utils.get(guild.roles, name="Muted")

        if not muted:
            muted = await guild.create_role(name="Muted")
            for channel in guild.channels:
                await channel.set_permissions(muted, speak=False, send_messages=False, read_message_history=True,
                                              read_messages=False)
        await user.add_roles(muted, reason=reason)
        await ctx.send(f"{user.mention} Was muted by {ctx.author.name} for {mute_time} min\n"
                       f"Reason: {reason}", delete_after=10)
        await asyncio.sleep(duration)
        await user.remove_roles(muted)
        await ctx.send(f"{user.mention}'s mute is over", delete_after=10)

    # KICK FUNCTIONS
    @staticmethod
    async def operation(ctx, user: discord.Member, operation_t: str, reason=None):
        if user == ctx.author:
            return await ctx.send(
                f"{user.mention} You can't {operation_t} yourself", delete_after=5.0)
        if operation_t == "kick":
            await user.kick(reason=reason)
        elif operation_t == "ban":
            await user.ban(reason=reason)
        elif operation_t == "softban":
            await user.ban(reason=reason)
            await user.unban(reason=reason)

        if not reason:
            await ctx.send(f"{user} was {operation_t}ed", delete_after=10.0)
            await user.send(f"You were {operation_t}ed from {ctx.guild.name}")
        else:
            await ctx.send(f"{user} was {operation_t}ed\nReason: {reason}", delete_after=10.0)
            await user.send(f"You were {operation_t}ed from {ctx.guild.name}\nReason: {reason}")

    # Kick
    @cog_ext.cog_slash(name="kick", guild_ids=cogbase.GUILD_IDS,
                       description="Kicks member from the server",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_MODS)
    async def kick(self, ctx, user: discord.Member, *, reason=None):
        operation_t = "kick"
        await self.operation(ctx, user, operation_t, reason)

    # Ban
    @cog_ext.cog_slash(name="ban", guild_ids=cogbase.GUILD_IDS,
                       description="Bans member from the server",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_ADMINS)
    async def ban(self, ctx, user: discord.Member, *, reason=None):
        operation_t = "ban"
        await self.operation(ctx, user, operation_t, reason)

    # Softban
    @cog_ext.cog_slash(name="softban", guild_ids=cogbase.GUILD_IDS,
                       description="Bans and unbans the user, so their messages are deleted",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_MODS)
    async def softban(self, ctx, user: discord.Member, *, reason=None):
        operation_t = "softban"
        await self.operation(ctx, user, operation_t, reason)

    # OTHER
    # Slow mode
    @cog_ext.cog_slash(name="slowmode", guild_ids=cogbase.GUILD_IDS,
                       description="Enable slowmode on current channel",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_MODS)
    async def slowmode(self, ctx, seconds: int = 0):
        if seconds > 120:
            return await ctx.send(":no_entry: Amount can't be over 120 seconds")
        if seconds == 0:
            await ctx.channel.edit(slowmode_delay=seconds)
            a = await ctx.send("Slowmode is off for this channel")
            await a.add_reaction("a:redcard:871861842639716472")
        else:
            if seconds == 1:
                numofsecs = "second"
            else:
                numofsecs = "seconds"
            await ctx.channel.edit(slowmode_delay=seconds)
            confirm = await ctx.send(
                f"{ctx.author.display_name} set the channel slow mode delay to `{seconds}` {numofsecs}\n"
                f"To turn this off use /slowmode")
            await confirm.add_reaction("a:ResidentWitcher:871872130021736519")


def setup(bot: commands.Bot):
    bot.add_cog(AdminCog(bot))
