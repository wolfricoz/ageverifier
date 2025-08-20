"""Allowing and denying users based on age."""
import asyncio

import discord

from classes.lobbyprocess import LobbyProcess
from databases.controllers.ConfigData import ConfigData
from databases.controllers.HistoryTransactions import JoinHistoryTransactions
from databases.controllers.VerificationTransactions import VerificationTransactions
from databases.enums.joinhistorystatus import JoinHistoryStatus
from views.modals.inputmodal import send_modal


class ApprovalButtons(discord.ui.View):
    def __init__(self, age: int = None, dob: str = None, user: discord.Member = None):
        self.age = age
        self.dob = dob
        self.user = user
        super().__init__(timeout=None)
        button = discord.ui.Button(label='Help', style=discord.ButtonStyle.url, url='https://wolfricoz.github.io/ageverifier/lobby.html', emoji="❓")
        self.add_item(button)
    # TODO: 
    @discord.ui.button(label="Approve User", style=discord.ButtonStyle.green, custom_id="allow")
    async def allow(self, interaction: discord.Interaction, button: discord.ui.Button):
        """starts approving process"""
        await self.disable_buttons(interaction, button)
        if self.age is None or self.dob is None or self.user is None:
            await interaction.followup.send('The bot has restarted and the data of this button is missing. Please use the command.', ephemeral=True)
            return
        await interaction.followup.send("User approved.", ephemeral=True)
        # Share this with the age commands
        try:
            await LobbyProcess.approve_user(interaction.guild, self.user, self.dob, self.age, interaction.user.name)
        except discord.NotFound:
            await interaction.followup.send("User not found, please manually add them to the database.", ephemeral=True)

    @discord.ui.button(label="Flag for ID Check", style=discord.ButtonStyle.red, custom_id="ID")
    async def manual_id(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Flags user for manual id."""
        await self.disable_buttons(interaction, button, False)
        reason = await send_modal(interaction, confirmation="The user has been flagged", title="Why should the user be ID Checked?", max_length=1500)
        if self.user is None:
            await interaction.followup.send('The bot has restarted and the data of this button is missing. Please manually report user to admins',
                                            ephemeral=True)
        await interaction.followup.send('User flagged for manual ID.', ephemeral=True)
        idcheck = ConfigData().get_key_int(interaction.guild.id, "idlog")
        idlog = interaction.guild.get_channel(idcheck)
        VerificationTransactions().set_idcheck_to_true(self.user.id, f"manually flagged by {interaction.user.name} with reason: {reason}", server=interaction.guild.name)
        JoinHistoryTransactions().update(self.user.id, interaction.guild.id, JoinHistoryStatus.IDCHECK)
        await interaction.message.edit(view=self)
        await idlog.send(
                f"{interaction.user.mention} has flagged {self.user.mention} for manual ID with reason:\n"
                f"```{reason}```")
        return

    @discord.ui.button(label="NSFW Profile Warning", style=discord.ButtonStyle.danger, custom_id="NSFW")
    async def nsfw_warning(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Flags user for nsfw warning."""
        await self.disable_buttons(interaction, button)
        if self.user is None:
            await interaction.followup.send('The bot has restarted and the data of this button is missing. Please manually report user to admins',
                                            ephemeral=True)
        await interaction.followup.send('User flagged for NSFW Warning.', ephemeral=True)
        warning = f"""**NSFW Warning**\n
Hello, this is the moderation team for {interaction.guild.name}. As Discord TOS prohibits NSFW content anywhere that can be accessed without an age gate, we will have to ask that you inspect your profile and remove any NSFW content. This includes but is not limited to: 
* NSFW profile pictures 
* NSFW display names
* NSFW Biographies
* NSFW status messages
* NSFW Banners
* NSFW Pronouns
* and NSFW game activity. 

Once you've made these changes you may resubmit your age and date of birth. Thank you for your cooperation."""
        await self.user.send(warning)

        return

    @discord.ui.button(label="User Left (stores DOB)", style=discord.ButtonStyle.primary, custom_id="add")
    async def add_to_db(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Adds user to db"""
        age_log = ConfigData().get_key_int(interaction.guild.id, "lobbylog")
        await self.disable_buttons(interaction, button,  disable_add=True)
        if self.user is None:
            await interaction.followup.send('The bot has restarted and the data of this button is missing. Please add the user manually.',
                                            ephemeral=True)
        await LobbyProcess.age_log(self.user.id, self.dob, interaction)
        await interaction.message.add_reaction("✅")
        await interaction.followup.send('User added to database and this message will be deleted in 3 minutes.', ephemeral=True)
        await asyncio.sleep(180)
        await interaction.message.delete()
        return



    async def disable_buttons(self, interaction, button: discord.ui.Button = None, update= True, disable_add = False):
        """disables buttons"""
        self.manual_id.disabled = True
        self.manual_id.style = discord.ButtonStyle.grey

        self.allow.disabled = True
        self.allow.style = discord.ButtonStyle.grey

        self.nsfw_warning.disabled = True
        self.nsfw_warning.style = discord.ButtonStyle.grey

        button.style = discord.ButtonStyle.green
        if disable_add:
            self.add_to_db.disabled = True
            self.add_to_db.style = discord.ButtonStyle.grey

        if update is False:
            return
        await interaction.response.edit_message(view=self)


