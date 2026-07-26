import discord
from discord_py_utilities.messages import send_response

from classes.AgeCalculations import AgeCalculations
from classes.encryption import Encryption
from classes.lobbyprocess import LobbyProcess
from classes.support.queue import Queue
from databases.transactions.UserTransactions import UserTransactions


class CrossServerAccessButton(discord.ui.View) :
	"""Persistent view: lets staff admit a member who was ID verified in another server.

	The target member's id is stored in the embed footer so the view can be
	registered with bot.add_view() and keep working after a restart. Any state
	needed by the button is reloaded from that footer via load_data(), which is
	why the member argument is optional (it is only used to build the outgoing
	embed, not to handle the interaction).
	"""

	def __init__(self, member: discord.Member = None, text: str = "Missing Text") -> None :
		super().__init__(timeout=None)
		self.member = member
		self.text = text

	@discord.ui.button(label="Approve User", style=discord.ButtonStyle.green, custom_id="cross_server_allow")
	async def allow(self, interaction: discord.Interaction, button: discord.ui.Button) :
		"""Admits the member referenced in the embed footer."""
		if not interaction.user.guild_permissions.manage_roles :
			return await send_response(interaction, "You must have the \"manage_roles\" permission to execute this action!", ephemeral=True)

		if not await self.load_data(interaction) :
			return await send_response(interaction, "Can't load message data.", ephemeral=True)

		record = UserTransactions().get_user(self.member.id, deleted=True)
		if record is None :
			return await send_response(interaction, f"No verification record found for {self.member.name}.", ephemeral=True)

		date_of_birth = Encryption().decrypt(record.date_of_birth)
		age = AgeCalculations.dob_to_age(date_of_birth)

		Queue().add(LobbyProcess().approve_user(interaction.guild, self.member, date_of_birth, age, interaction.user.name))
		await self.disable_buttons(interaction)
		return await send_response(interaction, f"Approved {self.member.name}", ephemeral=True)

	async def load_data(self, interaction: discord.Interaction) -> bool :
		"""Resolve the target member from the embed footer (survives restarts)."""
		if len(interaction.message.embeds) < 1 :
			return False
		user_id = interaction.message.embeds[0].footer.text
		if not isinstance(user_id, str) or not user_id.isnumeric() :
			return False
		user_id = int(user_id)

		self.member = interaction.guild.get_member(user_id)
		if self.member is None :
			try :
				self.member = await interaction.guild.fetch_member(user_id)
			except discord.NotFound :
				return False

		return True

	async def disable_buttons(self, interaction: discord.Interaction) :
		"""Prevents the same notice being approved more than once."""
		for child in self.children :
			child.disabled = True
		try :
			await interaction.message.edit(view=self)
		except discord.HTTPException :
			pass

	def create_embed(self) -> discord.Embed :
		embed = discord.Embed(
			title="Cross-server ID verification Notice",
			description=self.text,
			colour=discord.Colour.blue()
		)
		embed.set_footer(text=self.member.id)

		return embed
