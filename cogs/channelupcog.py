import discord
from discord.ext import commands
from discord_slash import cog_ext, SlashContext

import cogs.cogbase as cogbase


class ChannelUpCog(cogbase.BaseCog):
    def __init__(self, base):
        super().__init__(base)

    # CHANNEL NAMES UPDATES
    # Total member channel name
    @cog_ext.cog_slash(name="updateTotalMembers", guild_ids=cogbase.GUILD_IDS,
                       description="Update total number of members",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_MODS)
    async def update_member_count_command(self, ctx: SlashContext) -> None:
        await self.bot.update_member_count(ctx)
        await ctx.send("Total Members count updated", hidden=True)

    # Commons channel name
    @cog_ext.cog_slash(name="updateCommons", guild_ids=cogbase.GUILD_IDS,
                       description="Update common channel name",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_MODS)
    async def update_common_ch_name(self, ctx: SlashContext) -> None:
        with open('./server_files/commons.txt') as f:
            try:
                commons = f.read().splitlines()
            except ValueError:
                print(ValueError)

        await self.update_commons_ch(ctx, commons)

        commons.append(commons.pop(commons.index(commons[0])))
        with open('./server_files/commons.txt', 'w') as f:
            for item in commons:
                f.write("%s\n" % item)

    async def update_commons_ch(self, ctx: SlashContext, commons) -> None:
        await ctx.defer()
        new_name = f"common {commons[0]}"
        common_ch = self.bot.get_channel(self.bot.ch_common)
        await discord.TextChannel.edit(common_ch, name=new_name)
        self.create_log_msg(f"Common channel name updated: {commons[0]}")
        await common_ch.send(f"Common changed: **{commons[0]}**")

    # N-Word spotted channel name
    # Doesn't work if used too many times in a short period of time
    @cog_ext.cog_slash(name="nightmareStatus", guild_ids=cogbase.GUILD_IDS,
                       description="Change Nightmare status channel name",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_ADMINS)
    async def rename_nightmare_channel(self, ctx: SlashContext, status: str) -> None:
        new_status = status
        channel = self.bot.get_channel(self.bot.ch_nightmare_killed)
        if new_status in channel.name:
            await ctx.send(f"{channel.name} has been changed", hidden=True)
        else:
            await discord.VoiceChannel.edit(channel, name=f"N-Word fixed: {new_status}")
            await ctx.send(f"{channel.name} channel name has been changed", hidden=True)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(ChannelUpCog(bot))
