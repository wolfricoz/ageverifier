import json
import logging
import os

import discord

from databases.transactions.ServerTransactions import ServerTransactions
from project.data import CACHE
from views.select.CommandSelect import CommandSelect


class HelpLayout(discord.ui.LayoutView) :
	"""This is the 2.0 embed layout for onboarding messages."""
	content = (
		"## AgeVerifier Configuration Guide\n\n"
		"Welcome to Age-Verifier! This guide will walk you through setting up the bot on your server. "
		"For the easiest experience, we recommend using our dashboard\n\n"
		"### Quick Start: Automatic Setup\n"
		"The fastest way to get started is with the automatic setup command. This will create the necessary channels and roles for you.\n"
		"```\n"
		"/config setup type:auto\n"
		"```\n"
		"After running this, you will have a basic working configuration.\n\n"
		"### Manual Configuration\n"
		"If you prefer to use your existing channels and roles, you can configure the bot manually. Here are the essential steps:\n\n"
		"**1. Set Up Channels**\n"
		"You need to tell the bot which channels to use for its functions. The most important ones are the `server_join_channel` (where new users land) and the `age_log` (for moderator actions and bot logs).\n"
		"```\n"
		"/config channels key:server_join_channel action:set value:<#your-lobby-channel>\n"
		"/config channels key:age_log action:set value:<#your-log-channel>\n"
		"```\n\n"
		"**2. Set Up Roles**\n"
		"Next, define the roles for verified and unverified users. The `server_join_role` is given to new members, and the `verification_add_role` is given after they successfully verify.\n"
		"```\n"
		"/config roles key:server_join_role action:VERIFICATION_ADD_ROLE value:<@your-unverified-role>\n"
		"/config roles key:verification_add_role action:VERIFICATION_ADD_ROLE value:<@your-verified-role>\n"
		"```\n"
		"You can also add roles that are assigned based on age:\n"
		"```\n"
		"/config roles key:VERIFICATION_ADD_ROLE action:VERIFICATION_ADD_ROLE value:<@your-age-specific-role> minimum_age:18 maximum_age:25\n"
		"```\n\n"
		"**3. Check Permissions**\n"
		"After setting up channels and roles, run the permission check to ensure the bot can operate correctly.\n"
		"```\n"
		"/config permissioncheck\n"
		"```\n"
		"The bot will report any missing permissions in your log channel.\n\n"
		"### Customization (Optional)\n"
		"You can further customize the bot to fit your server's needs:\n\n"
		"*   **Custom Messages**: Change the text of the messages the bot sends.\n"
		"    `/config messages key:<message_key> action:set`\n\n"
		"*   **Toggles**: Enable or disable features like the welcome message in the lobby.\n"
		"    `/config toggles key:send_join_message action:disabled`\n\n"
		"*   **Verification Cooldown**: Set a time limit between verification attempts for a user.\n"
		"    `/config cooldown cooldown:5` (sets a 5-minute cooldown)\n\n"
		"### View Your Configuration\n"
		"To see all your current settings at a glance, use the `view` command. It will send the configuration as a text file.\n"
		"```\n"
		"/config view\n"
		"```\n\n"
		"For more detailed information on every command and feature, click the documentation button!"
	)

	commands = []

	def __init__(self, content=None) :
		super().__init__(timeout=None)
		self.commands = []
		self.command_docs = {}
		if content :
			self.content = content
		self.reason = None
		self.interaction = None
		self.current_page = 0

		# Define components
		self.container = discord.ui.Container(
			discord.ui.TextDisplay(content=self.content),
			discord.ui.Separator(visible=True),
			accent_colour=discord.Colour.purple()
		)

		self.links = discord.ui.ActionRow()
		self.links.add_item(
			discord.ui.Button(label="Dashboard Setup", style=discord.ButtonStyle.link, url=os.getenv("DASHBOARD_URL")))
		self.links.add_item(discord.ui.Button(label="Documentation", style=discord.ButtonStyle.link,
		                                      url="https://wolfricoz.github.io/ageverifier/"))
		support_server = ServerTransactions().get(int(os.getenv("SUPPORTGUILD")))
		if support_server is not None :
			self.links.add_item(
				discord.ui.Button(label="Support Server", style=discord.ButtonStyle.link, url=support_server.invite))

		self.selectrow = discord.ui.ActionRow()
		self.buttonrow = discord.ui.ActionRow()

		# Add components to the view
		self.add_item(self.container)
		self.add_item(self.links)
		self.add_item(self.selectrow)
		self.add_item(self.buttonrow)

		self.reasons = []
		try :
			with open(CACHE, "r", encoding="utf-8") as cachefile :
				self.command_docs = json.load(cachefile)
		except (FileNotFoundError, json.JSONDecodeError) :
			self.command_docs = {"No Commands Found" : "The command documentation cache is missing or corrupted."}

		for command, description in self.command_docs.items() :
			self.reasons.append(discord.SelectOption(label=command, description=description[:100]))

		self.items_per_page = 25
		self.total_pages = (len(self.reasons) + self.items_per_page - 1) // self.items_per_page

		self._update_page()

	def _update_page(self) :
		logging.info(f"Updating page: {self.current_page}")
		# Clear the rows
		self.selectrow.clear_items()
		self.buttonrow.clear_items()

		# Calculate slice for current page
		start = self.current_page * self.items_per_page
		end = start + self.items_per_page
		page_reasons = self.reasons[start :end]

		# Add select menu to its own row
		select = CommandSelect(page_reasons, self)
		self.selectrow.add_item(select)

		# logging.info(f"Total pages: {self.total_pages}, Current page: {self.current_page}")

		if self.total_pages > 1 :
			# Previous button
			prev_button = discord.ui.Button(
				label="◀ Previous",
				style=discord.ButtonStyle.primary,
				disabled=(self.current_page == 0)
			)
			prev_button.callback = self._previous_page
			self.buttonrow.add_item(prev_button)

			# Page indicator
			page_button = discord.ui.Button(
				label=f"Page {self.current_page + 1}/{self.total_pages}",
				style=discord.ButtonStyle.secondary,
				disabled=True
			)
			self.buttonrow.add_item(page_button)

			# Next button
			next_button = discord.ui.Button(
				label="Next ▶",
				style=discord.ButtonStyle.primary,
				disabled=(self.current_page >= self.total_pages - 1)
			)
			next_button.callback = self._next_page
			self.buttonrow.add_item(next_button)

	async def _previous_page(self, interaction: discord.Interaction) :
		self.current_page = max(0, self.current_page - 1)
		self._update_page()
		await interaction.response.edit_message(view=self)

	async def _next_page(self, interaction: discord.Interaction) :
		self.current_page = min(self.total_pages - 1, self.current_page + 1)
		self._update_page()
		await interaction.response.edit_message(view=self)
