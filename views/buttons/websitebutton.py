import discord.ui


class WebsiteButton(discord.ui.View) :

	def __init__(self, url):
		super().__init__(timeout=None)
		button = discord.ui.Button(label='Verification Page', style=discord.ButtonStyle.url, url=url)
		self.add_item(button)
