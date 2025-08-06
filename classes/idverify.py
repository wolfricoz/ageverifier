from classes.AgeCalculations import AgeCalculations
from databases.controllers.VerificationTransactions import VerificationTransactions
from classes.lobbyprocess import LobbyProcess


async def verify(user, interaction, dob, process=True):
	if not interaction.user.guild_permissions.administrator:
		return False
	VerificationTransactions().idverify_update(user.id, dob, interaction.guild.name, server=interaction.guild.name)
	age = AgeCalculations.dob_to_age(dob)
	id_message = f"**USER ID VERIFICATION**\n**ID VERIFIED BY:** {interaction.user}\n"

	await LobbyProcess.log(user, interaction.guild, age, dob, interaction.user, True, id_verify=id_message)
	await interaction.channel.send(
		f"{user.mention} has been ID verified with `{dob}` by {interaction.user.mention}")
	if process is False:
		return None
	await LobbyProcess.approve_user(interaction.guild, user, dob, age, interaction.user.name, idverify=True)
	return None