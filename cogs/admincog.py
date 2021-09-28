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
                       description="Check bot's latency",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_MODS)
    async def check_ping(self, ctx: SlashContext):
        await ctx.send(f"Pong! {round(self.bot.latency * 1000)}ms", delete_after=4.0)

    # Clear messages
    @cog_ext.cog_slash(name="clear", guild_ids=cogbase.GUILD_IDS,
                       description="Clear messages on channel",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_MODS)
    async def purge_messages(self, ctx: SlashContext, number_to_delete: int = 1):
        messages = []
        async for message in ctx.channel.history(limit=number_to_delete + 1):
            messages.append(message)
        await ctx.channel.delete_messages(messages)
        await asyncio.sleep(5)
        await ctx.send(f"Cleared {number_to_delete} messages!", delete_after=3)


    # Disconnect Bot
    @cog_ext.cog_slash(name="exit", guild_ids=cogbase.GUILD_IDS,
                       description="Turn off the bot",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_ADMINS)
    async def exit_bot(self, ctx: SlashContext):
        await ctx.send(f"Closing Bot", delete_after=1.0)
        self.create_log_msg("Exiting Bot")
        await asyncio.sleep(3)
        await self.bot.close()

    # WARN FUNCTIONS

    # Warn user
    @cog_ext.cog_slash(name="warn", guild_ids=cogbase.GUILD_IDS,
                       description="Warn member",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_MODS)
    async def warn_user(self, ctx: SlashContext, user: discord.User, reason: str):

        await DatabaseCog.db_add_warn(user.id, reason)
        await ctx.send(
            f"{user.mention} was warned for:\n> {reason}\n")

    # Get list of user's warns
    @cog_ext.cog_slash(name="warns", guild_ids=cogbase.GUILD_IDS,
                       description="Get member warns",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_MODS)
    async def user_warns(self, ctx: SlashContext, user: discord.User):
        warns, nr_of_warns = await DatabaseCog.db_get_warns(user.id)
        nl = "\n"
        message = f"**{user.name}** has been warned **{nr_of_warns}** times\n\n_Reasons_:\n" \
                  f"{nl.join(warns)}\n"
        await ctx.author.send(message)
        await ctx.send(f"{user.name} warns has been sent to DM", hidden=True)

    # Remove all member's warns
    @cog_ext.cog_slash(name="removeWarns", guild_ids=cogbase.GUILD_IDS,
                       description="Remove all member's warns",
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
    async def mute_user(self, ctx: SlashContext, user: discord.User, mute_time: int, reason: str):
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
        reason_str = f"\nReason: {reason}" if reason else ""

        await ctx.send(f"{user} was {operation_t}ed{reason_str}")
        await user.send(f"You were {operation_t}ed from {ctx.guild.name}{reason_str}")

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
                       description="Ban member from the server",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_ADMINS)
    async def ban(self, ctx, user: discord.Member, *, reason=None):
        operation_t = "ban"
        await self.operation(ctx, user, operation_t, reason)

    # Softban
    @cog_ext.cog_slash(name="softban", guild_ids=cogbase.GUILD_IDS,
                       description="Ban and unban the user, so their messages are deleted",
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
