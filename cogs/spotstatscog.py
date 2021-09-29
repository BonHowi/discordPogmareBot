import discord
from discord.ext import commands, tasks
from discord.utils import get
from cogs import cogbase
from collections import Counter, OrderedDict
from discord_slash import cog_ext, SlashContext
from functools import reduce


class SpotStatsCog(cogbase.BaseCog):
    def __init__(self, base):
        super().__init__(base)
        self.hex_to_int = "%02x%02x%02x"
        self.lege_total = 0
        self.rare_total = 0
        self.common_total = 0
        self.update_spot_stats_loop.start()

    async def update_spot_stats(self, channel_id: int, channel_type: int):
        spot_stats_ch = self.bot.get_channel(self.bot.ch_spotting_stats)

        roles_main_list = await self.get_channel_history(channel_id, channel_type)
        roles_werewolf_list = await self.get_channel_history(self.bot.ch_werewolf, channel_type)
        roles_wraith_list = await self.get_channel_history(self.bot.ch_wraiths, channel_type)
        roles_joined_list = roles_main_list + roles_werewolf_list + roles_wraith_list

        roles_counter = Counter(roles_joined_list)
        roles_counter = OrderedDict(roles_counter.most_common())
        top_print = []
        total = 0
        for key, value in roles_counter.items():
            spotting_stats = [f"{key}:  **{value}**"]
            top_print.append(spotting_stats)
            total += value

        top_print = ['\n'.join([elem for elem in sublist]) for sublist in top_print]
        top_print = "\n".join(top_print)

        if channel_type == 1:
            embed_title = "LEGENDARY"
            embed_color = int(self.hex_to_int % (163, 140, 21), 16)
            self.lege_total = total
        elif channel_type == 0:
            embed_title = "RARE"
            embed_color = int(self.hex_to_int % (17, 93, 178), 16)
            self.rare_total = total
        else:
            embed_title = "OTHER"
            embed_color = int(self.hex_to_int % (1, 1, 1), 16)

        embed_command = discord.Embed(title=f"{embed_title}", description=top_print, color=embed_color)
        embed_command.add_field(name="Total", value=f"**{total}**", inline=False)
        dt_string = self.bot.get_current_time()
        embed_command.set_footer(text=f"{dt_string}")
        await spot_stats_ch.send(embed=embed_command)

        channel = self.bot.get_channel(channel_id)
        self.create_log_msg(f"Spotting stats updated - {channel.name}")

    async def get_channel_history(self, channel_id, channel_type) -> list:
        guild = self.bot.get_guild(self.bot.guild[0])
        channel = self.bot.get_channel(channel_id)
        roles_list = []
        async for message in channel.history(limit=None, oldest_first=True):
            if message.content.startswith("<@&8"):  # If message is a ping for a role
                seq_type = type(message.content)
                role_id = int(seq_type().join(filter(seq_type.isdigit, message.content)))
                role = get(guild.roles, id=role_id)
                if role:
                    roles_list.append(self.create_spotted_list(role, channel_type))
        roles_list = list(filter(None, roles_list))
        return roles_list

    def create_spotted_list(self, role, channel_type):
        monster_found = None
        for monster in self.bot.config["commands"]:
            if monster["name"].lower() == role.name.lower() or role.name.lower() in monster["triggers"]:
                monster_found = monster
                break
        if monster_found["type"] == channel_type:
            return role.name

    @tasks.loop(hours=12)
    async def update_spot_stats_loop(self):
        spot_stats_ch = self.bot.get_channel(self.bot.ch_spotting_stats)
        await spot_stats_ch.purge()
        await self.update_spot_stats(self.bot.ch_legendary_spot, 1)
        await self.update_spot_stats(self.bot.ch_rare_spot, 0)
        self.create_log_msg(f"All spotting stats updated")

    @update_spot_stats_loop.before_loop
    async def before_update_spot_stats_loop(self):
        self.create_log_msg(f"Waiting until Bot is ready")
        await self.bot.wait_until_ready()

    # TODO: make this database function
    # TODO: code refactoring
    # Member own stats
    @cog_ext.cog_slash(name="mySpottingStats", guild_ids=cogbase.GUILD_IDS,
                       description=" ",
                       default_permission=True
                        # , permissions=cogbase.PERMISSION_MODS
                       )
    async def get_spotting_stats(self, ctx):
        await ctx.send("Generating spots stats", delete_after=5)
        guild = self.bot.get_guild(self.bot.guild[0])
        channel = self.bot.get_channel(self.bot.ch_logs)
        leges_list = []
        rares_list = []
        async for message in channel.history(limit=None, oldest_first=True):
            if message.content.startswith("[PingLog]") and str(ctx.author.id) in message.content:
                for monster in self.bot.config["commands"]:
                    if monster["name"] in message.content:
                        monster_name = monster["name"]
                print(monster_name)
                role = get(guild.roles, name=monster_name)
                if role:
                    leges_list.append(self.create_spotted_list(role, 1))
                    rares_list.append(self.create_spotted_list(role, 0))

        leges_list = list(filter(None, leges_list))
        leges_counter = Counter(leges_list)
        leges_counter = OrderedDict(leges_counter.most_common())
        leges_print = []
        leges_total = 0
        for key, value in leges_counter.items():
            spotting_stats = [f"{key}:  **{value}**"]
            leges_print.append(spotting_stats)
            leges_total += value
        leges_print = ['\n'.join([elem for elem in sublist]) for sublist in leges_print]
        leges_print = "\n".join(leges_print)
        leges_color = int(self.hex_to_int % (163, 140, 21), 16)
        embed_command = discord.Embed(title=f"Legendary", description=leges_print, color=leges_color)
        embed_command.add_field(name="Total", value=f"**{leges_total}**", inline=False)
        if self.lege_total != 0:
            percentage_leges = round(leges_total / self.lege_total * 100, 2)
            embed_command.add_field(name="Server %", value=f"**{percentage_leges}%**", inline=False)
        dt_string = self.bot.get_current_time()
        embed_command.set_footer(text=f"{dt_string}")
        await ctx.author.send(embed=embed_command)

        rares_list = list(filter(None, rares_list))
        rares_counter = Counter(rares_list)
        rares_counter = OrderedDict(rares_counter.most_common())
        rares_print = []
        rares_total = 0
        for key, value in rares_counter.items():
            spotting_stats = [f"{key}:  **{value}**"]
            rares_print.append(spotting_stats)
            rares_total += value
        rares_print = ['\n'.join([elem for elem in sublist]) for sublist in rares_print]
        rares_print = "\n".join(rares_print)
        rares_color = int(self.hex_to_int % (17, 93, 178), 16)
        embed_command = discord.Embed(title=f"Rare", description=rares_print, color=rares_color)
        embed_command.add_field(name="Total", value=f"**{rares_total}**", inline=False)
        if self.rare_total != 0:
            percentage_rares = round(rares_total / self.rare_total * 100, 2)
            embed_command.add_field(name="Server %", value=f"**{percentage_rares}%**", inline=False)
        dt_string = self.bot.get_current_time()
        embed_command.set_footer(text=f"{dt_string}")
        await ctx.author.send(embed=embed_command)

        common_ch = self.bot.get_channel(self.bot.ch_common)
        common_total = 0
        async for message in common_ch.history(limit=None, oldest_first=True):
            self.common_total += 1
            if ctx.author == message.author:
                common_total += 1
        embed_command = discord.Embed(title=f"Common")
        embed_command.add_field(name="Total", value=f"**{common_total}**", inline=False)
        if self.common_total != 0:
            percentage_common = round(common_total / self.common_total * 100, 2)
            embed_command.add_field(name="Server %", value=f"**{percentage_common}%**", inline=False)
        dt_string = self.bot.get_current_time()
        embed_command.set_footer(text=f"{dt_string}")
        await ctx.author.send(embed=embed_command)
        self.create_log_msg(f"Spotting stats created for {ctx.author}")


def setup(bot: commands.Bot):
    bot.add_cog(SpotStatsCog(bot))
