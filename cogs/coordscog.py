from discord.ext import commands
from discord_slash import cog_ext
import pandas as pd

from cogs import cogbase


class CoordsCog(cogbase.BaseCog):
    def __init__(self, base):
        super().__init__(base)

    @cog_ext.cog_slash(name="saveCoordinates", guild_ids=cogbase.GUILD_IDS,
                       description="Save spotting coordinates from channels history",
                       default_permission=False,
                       permissions=cogbase.PERMISSION_ADMINS)
    async def save_coordinates(self, ctx):
        await ctx.send(f"Coords are being saved", hidden=True)
        legendary_coords = await self.get_channel_history(self.bot.ch_legendary_spot)
        rare_coords = await self.get_channel_history(self.bot.ch_rare_spot)
        # werewolf_coords = await self.get_channel_history(self.bot.ch_werewolf)
        # wraith_coords = await self.get_channel_history(self.bot.ch_wraiths)
        common_coords = await self.get_channel_history(self.bot.ch_common)
        # TODO: why does concat create list instead of df???

        # coords_list = [legendary_coords, rare_coords, common_coords]
        # result = pd.concat(coords_list, ignore_index=True)
        coords_df = legendary_coords.append(rare_coords).append(common_coords)
        path_coords = r"server_files/coords_history.xlsx"
        coords_df.to_excel(path_coords, index=False)
        self.create_log_msg(f"Coords saved to {path_coords}")

    async def get_channel_history(self, channel_id):
        channel = self.bot.get_channel(channel_id)
        coords_list = []
        async for message in channel.history(limit=None, oldest_first=True):
            # TODO: there is probably better way to do it
            coords_filter_list = ["0.", "1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9."]
            is_coord = [ele for ele in coords_filter_list if (ele in message.content)]
            if is_coord:
                coords_list.append(message.content)
        coords_list = [i.split('\n') for i in coords_list]
        coords_list = [item for sublist in coords_list for item in sublist]
        coords_list = list(filter(None, coords_list))
        coords_df = pd.DataFrame(coords_list, columns=["coords"])
        coords_df["type"] = "common" if "common" in channel.name else channel.name
        return coords_df


def setup(bot: commands.Bot):
    bot.add_cog(CoordsCog(bot))
