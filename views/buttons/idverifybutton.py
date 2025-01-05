import discord




class IdVerifyButton(discord.ui.View) :
	def __init__(self) :
		super().__init__(timeout=None)

	@discord.ui.button(label="ID Verify", style=discord.ButtonStyle.green, custom_id="id_verify")
	async def idverify(self, interaction: discord.Interaction, button: discord.ui.Button) :
		raise NotImplementedError

	@discord.ui.button(label="Remove ID Check", style=discord.ButtonStyle.red, custom_id="remove")
	async def remove(self, interaction: discord.Interaction, button: discord.ui.Button) :
		raise NotImplementedError
