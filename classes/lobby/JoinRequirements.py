import logging
from datetime import UTC, datetime, timedelta

import discord
from discord.ext.commands import Bot
from discord_py_utilities.messages import send_message

from classes.access import AccessControl
from classes.banwatch import BanWatch
from classes.support.queue import Queue
from databases.transactions.ConfigData import ConfigData
from databases.transactions.ServerTransactions import ServerTransactions
from resources.data.config_variables import FAIL_ACTION


class JoinRequirements :

	def __init__(self, bot: Bot, member: discord.Member) -> None :
		self.bot = bot
		self.member = member
		self.status = None
		self.reason = None

	# === Main functions ===

	async def evaluate(self) -> None :
		# Check is guild is premium
		if not AccessControl().is_premium(self.member.guild.id):
			return None
		# Refresh the member to fetch latest data from the api.
		await self.refresh_member()

		# setting up variables.
		self.status = None
		self.reason = None
		logging.info("JoinRequirements: Checking on join")
		# executing checks
		await self.execute_action(self.check_account_age)
		await self.execute_action(self.check_has_avatar)
		await self.execute_action(self.check_mutual_guilds)
		await self.execute_action(self.check_is_bot)
		await self.execute_action(self.check_has_bans)
		await self.execute_action(self.check_require_active_presence)
		await self.execute_action(self.check_filter_web_only_accounts)

		logging.info(f"JoinRequirements: result: {self.status}, reason: {self.reason}")

		if self.status and self.reason :
			logging.info(f"JoinRequirements: taking actions")
			# Setting up kick variables; these are only used when actually needing to kick.
			server = ServerTransactions().get(self.member.guild.id)
			invite = "No invite set"
			lobby_channel = await ConfigData().get_channel(self.member.guild, "VERIFICATION_FAILURE_LOG")
			if not lobby_channel :
				logging.info(f"JoinRequirements: Lobby channel not set.")
				return None
			if server :
				invite = server.invite
			removal_message = (
				f"**Removed from {self.member.guild.name}**\n\n"
				f"**Reason:** {self.reason}\n\n"
				f"If you'd like to rejoin once resolved, use this link: {invite}"
			)
			action = ConfigData().get_key(self.member.guild.id, FAIL_ACTION, "LOG")

			if action.lower() == "kick" :
				Queue().add(send_message(self.member, removal_message))
				Queue().add(self.member.kick(reason=self.reason))


			Queue().add(send_message(lobby_channel, " ", embed=self.create_embed(action)))
		return None

	async def execute_action(self, check) -> None :
		if self.status :
			return
		await check()

	# === Check functions ===

	async def check_account_age(self) -> bool :
		# config
		days = ConfigData().get_key(self.member.guild.id, "MINIMUM_ACCOUNT_AGE", 7)
		enabled = ConfigData().get_toggle(self.member.guild.id, "ACCOUNT_AGE")
		if not enabled :
			return False

		created_at = self.member.created_at.astimezone(UTC)
		cut_off = datetime.now(UTC) - timedelta(days=days)
		if created_at > cut_off :
			self.status = True
			self.reason = f"Account is younger than {days} days."
			return True
		return False

	async def check_has_avatar(self) -> bool :
		enabled = ConfigData().get_toggle(self.member.guild.id, "HAS_AVATAR")
		if not enabled :
			return False

		if self.member.avatar is None or self.member.avatar == self.member.default_avatar :
			self.status = True
			self.reason = "Account does not have a profile avatar. If you recently updated your avatar, please wait up to 30 minutes before rejoining to allow Discord's API to sync."
			return True
		return False

	async def check_mutual_guilds(self) -> bool :
		enabled = ConfigData().get_toggle(self.member.guild.id, "MUTUAL_GUILDS")
		if not enabled :
			return False

		# min_mutuals = ConfigData().get_key(self.member.guild.id, "MINIMUM_MUTUAL_GUILDS", 1)
		min_mutuals = 1
		if len(self.member.mutual_guilds) < min_mutuals :
			self.status = True
			self.reason = f"Account shares fewer than {min_mutuals} mutual servers with the bot."
			return True
		return False

	async def check_is_bot(self) -> bool :
		enabled = ConfigData().get_toggle(self.member.guild.id, "IS_BOT")
		if not enabled :
			return False

		# If it's a normal user, they pass the check
		if not self.member.bot :
			return False

		inviter = None

		# Check audit logs to find who authorized the bot
		if self.member.guild.me.guild_permissions.view_audit_log :
			try :
				async for entry in self.member.guild.audit_logs(action=discord.AuditLogAction.bot_add, limit=5) :
					if entry.target.id == self.member.id :
						inviter = entry.user
						break
			except discord.Forbidden :
				pass

		if inviter :
			# Resolve the inviter to a Member object to accurately check guild permissions
			inviter_member = self.member.guild.get_member(inviter.id)

			# If the inviter is found and has Administrator permissions, allow the bot
			if inviter_member and inviter_member.guild_permissions.administrator :
				return False
			self.status = True
			self.reason = f"Unapproved Discord application. Added by a non-administrator: {inviter} ({inviter.id})."
		else :
			self.status = True
			self.reason = "Unapproved Discord application. Inviter could not be verified (Missing Audit Log permissions or not found)."

		return True  # Failed the check

	async def check_has_bans(self) -> bool :
		enabled = ConfigData().get_toggle(self.member.guild.id, "HAS_BANS")
		if not enabled :
			return False
		bans = await BanWatch().fetchBanCount(self.member.id)
		if bans and bans > 0 :
			self.status = True
			self.reason = f"User has {bans} ban(s) recorded in banwatch."

		return False

	async def check_require_active_presence(self) -> bool :
		enabled = ConfigData().get_toggle(self.member.guild.id, "REQUIRE_ACTIVE_PRESENCE")
		if not enabled :
			return False
		if not self.bot.intents.presences:
			return False

		if self.member.status == discord.Status.offline :
			self.status = True
			self.reason = "Account is offline or invisible."
			return True
		return False

	async def check_filter_web_only_accounts(self) -> bool :
		enabled = ConfigData().get_toggle(self.member.guild.id, "FILTER_WEB_ONLY_ACCOUNTS")
		if not enabled :
			return False
		if not self.bot.intents.presences:
			return False
		# Fails if web client is active but mobile and desktop status are both offline
		if (self.member.web_status != discord.Status.offline and
				self.member.desktop_status == discord.Status.offline and
				self.member.mobile_status == discord.Status.offline) :
			self.status = True
			self.reason = "Account is connected via Web Client only."
			return True
		return False


	def create_embed(self, action)-> discord.Embed:
		# Determine color and dynamic title based on the action
		is_kick = action.lower() == "kick"
		embed_color = discord.Color.red() if is_kick else discord.Color.orange()
		embed_title = "🛑 Join Requirement Failure" if is_kick else "⚠️ Join Requirement Warning"

		# Create the embed
		embed = discord.Embed(
			title=embed_title,
			color=embed_color,
			timestamp=discord.utils.utcnow()  # Adds a clean timestamp at the bottom
		)

		# User information section
		embed.add_field(
			name="User",
			value=f"{self.member.mention}\n`{self.member.id}`",
			inline=True
		)

		# Action taken section
		embed.add_field(
			name="Action Taken",
			value=f"`KICKED`" if is_kick else "`LOGGED`",
			inline=True
		)

		# Reason section (takes up the full width below the fields)
		embed.add_field(
			name="Reason",
			value=self.reason,
			inline=False
		)

		if self.member.avatar :
			embed.set_thumbnail(url=self.member.avatar.url)

		embed.set_footer(text="Security Log")
		return embed

	async def refresh_member(self):
		try:
			self.member = await self.member.guild.fetch_member(self.member.id)
		except:
			self.member = self.member