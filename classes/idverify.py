import discord
from torch.distributed.argparse_util import env

from classes.AgeCalculations import AgeCalculations
from classes.lobbyprocess import LobbyProcess
from classes.retired.discord_tools import send_message, send_response
from databases.transactions.VerificationTransactions import VerificationTransactions


async def verify(user: discord.Member, interaction: discord.Interaction, dob: str, process=True):
	if await check_staff_status(interaction, user):
		await send_response(interaction,
		                    f"[CANNOT_VERIFY_STAFF] You cannot verify staff members using this command, if they wish to be verified they can open a ticket on the support guild. Attempting to circumvent this guideline will result in permanent blacklisting of all users involved.", )

	if not interaction.user.guild_permissions.administrator:
		return False
	VerificationTransactions().idverify_update(user.id, dob, interaction.guild.name, server=interaction.guild.name)
	age = AgeCalculations.dob_to_age(dob)
	dev_log = interaction.client.get_channel(env("DEV", 1022319186950758472))
	if dev_log is None:
		dev_log = interaction.client.fetch_channel(env("DEV", 1022319186950758472))
	id_message = f"**USER ID VERIFICATION**\n**ID VERIFIED BY:** {interaction.user}\n"

	await LobbyProcess.log(user, interaction.guild, age, dob, interaction.user, True, id_verify=id_message)
	await interaction.channel.send(
		f"{user.mention} has been ID verified with `{dob}` by {interaction.user.mention}")
	if not process :
		return None
	if interaction.guild is None:
		return None

	await LobbyProcess.approve_user(interaction.guild, user, dob, age, interaction.user.name, idverify=True)
	if not dev_log:
		return None
	await send_message(dev_log, f"{user.global_name} ({user.id}) has been ID verified by {interaction.user} in {interaction.guild.name}!")
	return None


async def check_staff_status(interaction: discord.Interaction, member: discord.Member)->bool:
	if member.guild_permissions.manage_guild or member.guild_permissions.manage_permissions or member.guild_permissions.manage_messages or member.guild_permissions.manage_roles or member.guild_permissions.kick_members or member.guild_permissions.ban_members or member.guild_permissions.administrator :
		return True
	if interaction.guild.owner_id == member.id :
		return True
	return False