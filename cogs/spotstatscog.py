import discord
from discord.ext import commands, tasks
from discord.utils import get
from cogs import cogbase
from collections import Counter, OrderedDict


class SpotStatssCog(cogbase.BaseCog):
    def __init__(self, base):
        super().__init__(base)
        self.update_spot_stats_loop.start()

    async def update_spot_stats(self, channel_id: int, channel_type: int):
        spot_stats_ch = self.bot.get_channel(self.bot.ch_spotting_stats)
        hex_to_int = "%02x%02x%02x"
        # TODO: ...
        if channel_type == 1:
            embed_title = "LEGENDARY"
            embed_color = int(hex_to_int % (163, 140, 21), 16)
        elif channel_type == 0:
            embed_title = "RARE"
            embed_color = int(hex_to_int % (17, 93, 178), 16)
        else:
            embed_title = "???"
            embed_color = int(hex_to_int % (1, 1, 1), 16)

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


def setup(bot: commands.Bot):
    bot.add_cog(SpotStatssCog(bot))
