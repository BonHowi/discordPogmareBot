"""
Cog with role related commands available in the Bot.

Current commands:
/role

"""
import discord
import cogs.cogbase as cogbase
from discord.utils import get
from discord.ext import commands
from discord_slash import cog_ext, SlashContext

from modules.utils import get_dominant_color


class RequestCog(cogbase.BaseCog):
    def __init__(self, base):
        super().__init__(base)

    # Print available roles/commands on monster-request channel
    @commands.Cog.listener()
    async def on_ready(self):
        role_ch = self.bot.get_channel(self.bot.ch_role_request)
        await role_ch.purge(limit=10)
        bot = get(self.bot.get_all_members(), id=self.bot.user.id)
        bot_color = get_dominant_color(bot.avatar_url)

        for mon_type in self.bot.config["types"]:
            if mon_type["id"] in [2, 3, 4]:  # Pass if common/...
                continue

            aval_commands = []
            for command in self.bot.config["commands"]:
                if command["type"] == mon_type["id"]:
                    aval_commands.append(command["name"])

            hex_to_int = "%02x%02x%02x"
            if mon_type["id"] == 1:
                embed_color = int(hex_to_int % (163, 140, 21), 16)
            elif mon_type["id"] == 0:
                embed_color = int(hex_to_int % (17, 93, 178), 16)
            else:
                embed_color = bot_color

            embed_command = discord.Embed(title=mon_type["label"],
                                          description='\n'.join(aval_commands),
                                          color=embed_color)
            await role_ch.send(embed=embed_command)

        guide_content = "**/role monstername** - " \
                        "get role with monster name to be notified when the monster is spotted, " \
                        "use again to remove the role"
        embed_guide = discord.Embed(title="Channel Guide", description=guide_content, color=bot_color)
        embed_guide.set_footer(text="Check #guides for more info")
        await role_ch.send(embed=embed_guide)

    # Remove normal messages from monster-request channel
    @commands.Cog.listener()
    async def on_message(self, ctx):
        if ctx.author.id == self.bot.user.id:
            return

        if ctx.channel.id == self.bot.ch_role_request:
            if ctx.content.startswith("/"):
                await ctx.channel.send(
                    f"{ctx.author.mention} For adding or removing role use */role monstername* command",
                    delete_after=10.0)
            await ctx.delete()

    # Add or remove monster role to an user
    @cog_ext.cog_slash(name="role", guild_ids=cogbase.GUILD_IDS,
                       description="Get or remove role with monster name to be pinged when the monster is spotted",
                       default_permission=True)
    async def _role(self, ctx: SlashContext, name: str):
        if ctx.channel.id != self.bot.ch_role_request:
            await ctx.send(f"Use <#{self.bot.ch_role_request}> to request a role!", hidden=True)

        else:
            monster = self.get_monster(ctx, name)
            member = ctx.author
            if monster:
                role = get(member.guild.roles, name=monster["name"])
                if role in member.roles:
                    await member.remove_roles(role)
                    await ctx.send(f"{role} role removed", delete_after=10.0)
                else:
                    await member.add_roles(role)
                    await ctx.send(f"{role} role added", delete_after=10.0)
            else:
                await ctx.send(f"Monster role not found", delete_after=10.0)


def setup(bot: commands.Bot):
    bot.add_cog(RequestCog(bot))
