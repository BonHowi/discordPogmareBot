"""
Cog with role related commands available in the Bot.

Current commands:
/

"""
import discord
from discord.utils import get
from discord_slash.utils.manage_commands import create_permission
from dotenv import load_dotenv
import os
from discord.ext import commands
from discord_slash import cog_ext, SlashContext
from discord_slash.model import SlashCommandPermissionType
import json
from cogs.base import BaseCog
from modules.get_settings import get_settings

guild_ids = get_settings("guild")


class RoleCog(BaseCog):
    def __init__(self, base):
        super().__init__(base)

    # Print available roles/commands on monster-request
    @commands.Cog.listener()
    async def on_ready(self):
        role_channel = self.bot.get_channel(self.bot.CH_ROLE_REQUEST)
        await role_channel.purge(limit=10)

        for mon_type in self.bot.config["types"]:
            if mon_type["id"] in [4]:    # Pass if common/...
                continue

            aval_commands = []
            for command in self.bot.config["commands"]:
                if command["type"] == mon_type["id"]:
                    aval_commands.append(command["name"])

            embed_command = discord.Embed(title=mon_type["label"], description='\n'.join(aval_commands), color=0x00ff00)
            # embed_var.add_field(name="Field1", value="hi", inline=False)
            # embed_var.add_field(name="Field2", value="hi2", inline=False)
            await role_channel.send(embed=embed_command)

        guide_content = "TBA"
        embed_guide = discord.Embed(title="Channel Guide", description=guide_content)
        await role_channel.send(embed=embed_guide)

    # Remove normal messages from monster-request
    @commands.Cog.listener()
    async def on_message(self, ctx):
        if ctx.author.id == self.bot.user.id:
            return
        if ctx.channel.id == self.bot.CH_ROLE_REQUEST:
            if ctx.content.startswith("/"):
                await ctx.channel.send(f"{ctx.author.mention} **For adding or removing role use /role monstername**", delete_after=10.0)
                await ctx.delete()
            else:
                await ctx.delete()

    # Find monster in config
    async def get_monster(self, ctx: SlashContext, name: str):
        monster = []
        name = name.lower()

        for monsters in self.bot.config["commands"]:
            if monsters["name"].lower() == name:
                monster = monsters
                pass
            for monster_triggers in monsters["triggers"]:
                if monster_triggers == name:
                    monster = monsters

        if not monster:
            print("Monster not found")
            await ctx.send(f"Monster not found", hidden=True)
            return

        monster["role"] = discord.utils.get(ctx.guild.roles, name=monster["name"])
        if not monster["role"]:
            print(f"Failed to fetch roleID for monster {monster['name']}")
            await ctx.send(f"Role not found", hidden=True)
            return
        else:
            monster["role"] = monster["role"].id
        # print(monster["name"])
        # print(monster["role"])
        return monster

    # Add or remove monster role to an user
    @cog_ext.cog_slash(name="role", guild_ids=guild_ids,
                       description="Function for adding monster role to user",
                       default_permission=True)
    async def _role(self, ctx: SlashContext, monster_name: str):
        if ctx.channel.id != self.bot.CH_ROLE_REQUEST:
            await ctx.send(f"Use <#{self.bot.CH_ROLE_REQUEST}> to request a role!", hidden=True)
            return
        else:
            monster = await self.get_monster(ctx, monster_name)
            member = ctx.author
            if monster:
                role = get(member.guild.roles, name=monster["name"])
                if role in member.roles:
                    await member.remove_roles(role)
                    await ctx.send(f"{role} role removed", delete_after=3.0)
                else:
                    await member.add_roles(role)
                    await ctx.send(f"{role} role added", delete_after=3.0)
            else:
                await ctx.send(f"Monster role not found", delete_after=3.0)


def setup(bot: commands.Bot):
    bot.add_cog(RoleCog(bot))
