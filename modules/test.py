import discord
from discord import app_commands
from discord.ext import commands
from views.select.configselectroles import ConfigSelectRoles

# the base for a cog.
class Tools(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Your first app command!
    @app_commands.command(name='test')
    async def test(self, interaction: discord.Interaction):
        print("received")
        view = ConfigSelectRoles()
        value = await interaction.response.send_message("test", view=view)
        await view.wait()
        print(view.value)



async def setup(bot):
    await bot.add_cog(Tools(bot))



