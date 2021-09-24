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
        if channel_type == 1:
            embed_title = "LEGENDARY"
            embed_color = int('%02x%02x%02x' % (163, 140, 21), 16)
        elif channel_type == 0:
            embed_title = "RARE"
            embed_color = int('%02x%02x%02x' % (17, 93, 178), 16)
        else:
            embed_title = "???"
            embed_color = int('%02x%02x%02x' % (1, 1, 1), 16)

        roles_main_list = await self.get_channel_history(channel_id, channel_type)
        roles_event_list = await self.get_channel_history(self.bot.ch_werewolf, channel_type)
        roles_joined_list = roles_main_list + roles_event_list
        roles_counter = Counter(roles_joined_list)
        roles_counter = OrderedDict(roles_counter.most_common())
        top_print = []
        for key, value in roles_counter.items():
            spotting_stats = [f"**{key}**:  {value}"]
            top_print.append(spotting_stats)
        top_print = ['\n'.join([elem for elem in sublist]) for sublist in top_print]
        top_print = "\n".join(top_print)
        embed_command = discord.Embed(title=f"{embed_title}", description=top_print, color=embed_color)
        await spot_stats_ch.send(embed=embed_command)

    async def get_channel_history(self, channel_id, channel_type) -> list:
        guild = self.bot.get_guild(self.bot.guild[0])
        channel = self.bot.get_channel(channel_id)
        roles_list = []
        messages = await channel.history(limit=None, oldest_first=True).flatten()
        for message in messages:
            if message.content.startswith("<@&8"):
                seq_type = type(message.content)
                role_id = int(seq_type().join(filter(seq_type.isdigit, message.content)))
                role = get(guild.roles, id=role_id)
                if role:
                    monster_found = None
                    for monster in self.bot.config["commands"]:
                        if monster["name"].lower() == role.name.lower() or role.name.lower() in monster["triggers"]:
                            monster_found = monster
                            break
                    if monster_found["type"] == channel_type:
                        roles_list.append(role.name)
        return roles_list

    @tasks.loop(hours=12)
    async def update_spot_stats_loop(self):
        spot_stats_ch = self.bot.get_channel(self.bot.ch_spotting_stats)
        await spot_stats_ch.purge()
        await self.update_spot_stats(self.bot.ch_legendary_spot, 1)
        await self.update_spot_stats(self.bot.ch_rare_spot, 0)
        dt_string = self.bot.get_current_time()
        print(f"({dt_string})\t[{self.__class__.__name__}]: Spotting stats updated")

    @update_spot_stats_loop.before_loop
    async def before_update_spot_stats_loop(self):
        dt_string = self.bot.get_current_time()
        print(f'({dt_string})\t[{self.__class__.__name__}]: Waiting until Bot is ready')
        await self.bot.wait_until_ready()


def setup(bot: commands.Bot):
    bot.add_cog(SpotStatssCog(bot))
