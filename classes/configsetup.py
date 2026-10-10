import asyncio
import logging

import discord
from discord.utils import get
from discord_py_utilities.exceptions import NoPermissionException
from discord_py_utilities.messages import send_message, send_response
from discord_py_utilities.permissions import check_missing_channel_permissions, find_first_accessible_text_channel

from classes.config.utils import ConfigUtils
from classes.permissions_notice import AGEVERIFIER_PERMISSIONS_DOCS, DEFAULT_CHANNEL_PERMS, DISCORD_PERMISSIONS_DOCS, \
	describe_permission
from classes.support.queue import Queue
from databases.transactions.AgeRoleTransactions import AgeRoleTransactions
from databases.transactions.ConfigData import ConfigData
from databases.transactions.ConfigTransactions import ConfigTransactions
from resources.data.config_variables import available_toggles, channelchoices, messagechoices, rolechoices
from views.buttons.confirmButtons import confirmAction
from views.select.configselectroles import ConfigSelectChannels, ConfigSelectRoles


async def delete_quietly(msg: discord.Message) -> None :
	"""Deletes a setup prompt; staff often delete it themselves (or the channel) first (AGEVERIFIER-C7)."""
	try :
		await msg.delete()
	except (discord.NotFound, discord.Forbidden) :
		pass


class ConfigSetup :
	"""This class is used to setup the configuration for the bot"""
	rolechoices = rolechoices
	channelchoices = channelchoices
	messagechoices = messagechoices
	available_toggles = available_toggles

	def __init__(self) :
		# Per instance: a class-level dict was shared by every server's setup, leaking
		# one server's channel ids into another server's config-change log.
		self.changes = {}

	async def manual(self, bot, interaction: discord.Interaction, channelchoices: dict, rolechoices: dict,
	                 messagechoices: dict) :
		logging.info("Manual setup started")
		await interaction.response.defer(ephemeral=True)
		for channelkey, channelvalue in channelchoices.items() :
			view = ConfigSelectChannels()
			msg = await interaction.channel.send(f"Select a channel for {channelkey}: \n`{channelvalue}`", view=view)
			await view.wait()
			await delete_quietly(msg)
			try :
				if view.value == "next" :
					continue
				if view.value is None :
					await send_response(interaction, "Setup has been cancelled")
					return False
			except AttributeError :
				logging.info("No value found, message was deleted")
				return False
			self.changes[channelkey] = int(view.value[0])
			ConfigTransactions().config_unique_add(interaction.guild.id, channelkey, int(view.value[0]), overwrite=True)
		for key, value in rolechoices.items() :
			if key == "return_remove_role" :
				continue
			view = ConfigSelectRoles()
			msg = await interaction.channel.send(f"{key}: \n{value}", view=view)
			await view.wait()
			await delete_quietly(msg)
			try :
				if view.value == "next" :
					continue
				if view.value is None :
					await send_response(interaction, "Setup has been cancelled")
					return False
			except AttributeError :
				logging.info("No value found, message was deleted")
				return False
			self.changes[key] = int(view.value[0])
			ConfigTransactions().config_unique_add(interaction.guild.id, key, int(view.value[0]), overwrite=True)
		for messagekey, messagevalue in messagechoices.items() :
			msg = await interaction.channel.send(f"Please set the message for {messagekey}\n"
			                                     f"{messagevalue}\n"
			                                     f"Type `cancel` to cancel, or `next` to go to the next message")
			try :
				# Only this user in this channel: otherwise their next message anywhere,
				# even in another server, was taken as the answer and deleted.
				result = await bot.wait_for('message', timeout=1800,
				                            check=lambda m : m.author == interaction.user and m.channel == interaction.channel)
			except asyncio.TimeoutError :
				await delete_quietly(msg)
				await send_response(interaction, "Setup timed out, run `/config setup` to try again.")
				return False
			if result.content.lower() == "cancel" :
				await delete_quietly(msg)
				await send_response(interaction, "Setup has been cancelled")
				return False
			if result.content.lower() == "next" :
				await result.delete()
				await delete_quietly(msg)
				continue
			self.changes[messagekey] = result.content
			ConfigTransactions().config_unique_add(interaction.guild.id, messagekey, result.content, overwrite=True)
			await result.delete()
			await delete_quietly(msg)
		Queue().add(ConfigUtils.log_change(interaction.guild, self.changes, user_name=interaction.user.name), 1)
		return True

	async def auto(self, interaction: discord.Interaction, channelchoices: dict, rolechoices: dict,
	               messagechoices: dict) :
		logging.info("Auto setup started")
		confirmation = confirmAction()
		await confirmation.send_message(interaction,
		                                "Are you sure you want to automatically setup the configuration for this server? You may see new channels and roles created and some configuration still needs to be done manually.")
		await confirmation.wait()

		if not confirmation.confirmed :
			await send_response(interaction, "Setup has been cancelled")
			return False
		category = get(interaction.guild.categories, name="Lobby")
		if not category :
			category: discord.CategoryChannel = await interaction.guild.create_category(name="Lobby", overwrites={
				interaction.guild.default_role : discord.PermissionOverwrite(read_messages=False),
				interaction.guild.me           : discord.PermissionOverwrite(read_messages=True)
			})
		# False means the user cancelled a step and has already been told so.
		completed = await self.create_channels(interaction.guild, category, interaction) is not False
		if completed :
			completed = await self.create_roles(interaction.guild, rolechoices, interaction) is not False
		if completed :
			await self.set_messages(interaction.guild, messagechoices)
		Queue().add(ConfigUtils.log_change(interaction.guild, self.changes, user_name=interaction.user.name), 1)
		return completed

	async def add_roles_to_channel(self, channel, roles) :
		for r in roles :
			await channel.set_permissions(r, read_messages=True, send_messages=True)

	async def create_channels(self, guild, category, interaction=None) :
		channelchoices = self.channelchoices
		logging.info(channelchoices)
		if guild is None :
			logging.warning("Guild is None, cannot create channels")
			return None

		for channelkey, channelvalue in channelchoices.items() :
			channel = None
			logging.info("setting up channel: " + channelkey)
			try :
				match channelkey :
					case 'invite_log' :
						print("setting up invite info")
						channel = await self.create_channel(guild, category, "invite-info",
						                                    "This channel shows you additional join "
						                                    "information about the user.")

					case 'verification_completed_channel' :
						verification_completed_channel: discord.TextChannel = get(guild.text_channels, name="general")
						if verification_completed_channel :
							logging.info("setting up verification_completed_channel channel: ")
							self.changes[channelkey] = verification_completed_channel.id
							ConfigTransactions().config_unique_add(guild.id, channelkey, verification_completed_channel.id,
							                                       overwrite=True)
							continue
						if interaction is None :
							logging.info("Automated Setup, skipping verification_completed_channel channel")
							continue
						view = ConfigSelectChannels()
						msg = await interaction.channel.send(f"Select a channel for {channelkey}: \n`{channelvalue}`", view=view)
						await view.wait()
						await delete_quietly(msg)
						try :
							if view.value == "next" :
								continue
							if view.value is None :
								await send_response(interaction, "Setup has been cancelled")
								return False
						except AttributeError :
							logging.info("No value found, message was deleted")
							return False
						self.changes[channelkey] = int(view.value[0])
						ConfigTransactions().config_unique_add(guild.id, channelkey, int(view.value[0]), overwrite=True)
						continue
					# This is your general channel, where the welcome message will be posted
					case "server_join_channel" :
						# This is your lobby channel, where the lobby welcome message will be posted.
						# This is also where the verification process will start; this is where new users should interact with the bot.
						# this channel should be open to everyone.
						channel = await self.create_channel(guild, category, "lobby",
						                                    "This is where the users enter your server and are welcomed.")
						# await self.add_roles_to_channel(channel, roles)
						await channel.set_permissions(guild.default_role, read_messages=True, send_messages=True)

					case "age_log" :
						# This is the channel where the lobby logs will be posted.
						# This channel has to be hidden from the users; failure to do so will result in the bot leaving.
						channel = await self.create_channel(guild, category, "lobby-log",
						                                    "This is where the ages of the users are logged, this channel should never be public.")
					# await self.add_roles_to_channel(channel, roles)

					case "approval_channel" :
						# This is where the verification approval happens.
						# This channel should be hidden from the users.
						channel = await self.create_channel(guild, category, "lobby-moderation",
						                                    "This channel is where you approve your users and receive age-verifier related information. This channel should never be public.")
					# await self.add_roles_to_channel(channel, roles)

					case "verification_failure_log" :
						# This is where failed verification logs will be posted.
						# This channel should be hidden from the users.
						channel = await self.create_channel(guild, category, "id-check",
						                                    "This channel is where age discrepancies are flagged for ID verification. This channel should never be public.")
					# await self.add_roles_to_channel(channel, roles)
					case _ :
						continue


				try :
					if channel is None :
						if interaction is not None :
							await send_message(interaction.channel, f"Failed to create or find channel for {channelkey}, please set it up manually.")
						continue

					self.changes[channelkey] = channel.id
					ConfigTransactions().config_unique_add(guild.id, channelkey, channel.id, overwrite=True)
					# create_channels also runs on the automatic setup path where interaction
					# is None; only announce when a user triggered it (AGEVERIFIER-BJ).
					if interaction is not None :
						await send_message(interaction.channel, f"Channel for {channelkey} set to {channel.mention}")
					continue
				except Exception as e :
					logging.error(e, exc_info=True)
					continue
			except Exception as e :
				logging.error(e, exc_info=True)
				continue
		return True

	async def create_roles(self, guild, rolechoices, interaction=None) :
		skip_roles = ["RETURN_REMOVE_ROLE", "VERIFICATION_ADD_ROLE"]
		for key, value in rolechoices.items() :
			key = key.upper()
			if key == "RETURN_REMOVE_ROLE" :
				continue
			if key in skip_roles :
				if key == "VERIFICATION_ADD_ROLE" :
					if verified := [r for r in guild.roles if r.name.lower() == "verified"] :
						self.changes["VERIFICATION_ADD_ROLE"] = verified[0].id
						ConfigTransactions().config_unique_add(guild.id, "VERIFICATION_ADD_ROLE", verified[0].id, overwrite=True)
						continue
					verified = get(guild.roles, name="Verified")
					if verified is None :
						verified = await guild.create_role(name="Verified", reason="Setup")
					self.changes["VERIFICATION_ADD_ROLE"] = verified.id
					ConfigTransactions().config_unique_add(guild.id, "VERIFICATION_ADD_ROLE", verified.id, overwrite=True)
					continue

				continue
			if interaction is None :
				logging.info("Automated Setup, skipping role setup")
				continue
			view = ConfigSelectRoles()
			msg = await interaction.channel.send(f"{key}: \n{value}", view=view)
			await view.wait()
			await delete_quietly(msg)
			try :
				if view.value == "next" :
					continue
				if view.value is None :
					await send_response(interaction, "Setup has been cancelled")
					return False
			except AttributeError :
				logging.info("No value found, message was deleted")
				return False
			self.changes[key] = int(view.value[0])
			ConfigTransactions().config_unique_add(guild.id, key, int(view.value[0]), overwrite=True)
		return True

	async def set_messages(self, guild, messagechoices) :
		for messagekey, messagevalue in messagechoices.items() :
			message_dict = {
				'server_join_message'          : f"Please read the rules in the rules channel and click the verify button below to get started.",
				'verification_completed_message' : "Be sure to get some roles in the roles channel and if you need help be sure to ask the staff!",
				'server_leave_message': 'Thanks for hanging out with us! 👋'
			}
			default = message_dict.get(messagekey)
			if default is None :
				# Not every message has a starting text worth writing during setup; the
				# verification button label, for instance, already falls back on its own.
				continue
			self.changes[messagekey] = default
			ConfigTransactions().config_unique_add(guild.id, messagekey, default, overwrite=True)

	async def create_channel(self, guild, category, name, description=None) :
		channel = get(guild.text_channels, name=name)
		if not channel :
			channel = await category.create_text_channel(name=name)
		try :
			await channel.edit(topic=description)
		except discord.Forbidden :
			pass
		except Exception as e :
			logging.error(e, exc_info=True)
		return channel

	async def api_auto_setup(self, guild: discord.Guild) :
		category = get(guild.categories, name="Lobby")
		if not category :
			category: discord.CategoryChannel = await guild.create_category(name="Lobby", overwrites={
				guild.default_role : discord.PermissionOverwrite(read_messages=False),
				guild.me           : discord.PermissionOverwrite(read_messages=True)
			})
		# Run in order on this instance so self.changes is filled before it is logged and
		# the moderation channel exists before the completion notice is sent to it.
		await self.create_channels(guild, category)
		await self.create_roles(guild, rolechoices)
		await self.set_messages(guild, messagechoices)
		lobby_mod = guild.get_channel(ConfigData().get_key_int(guild.id, "approval_channel"))
		Queue().add(send_message(lobby_mod, f"## Auto Setup for {guild.name} has been completed!"), 0)
		Queue().add(send_message(guild.owner, f"## Auto Setup for {guild.name} has been completed!"), 0)
		Queue().add(ConfigUtils.log_change(guild, self.changes, user_name="Dashboard"), 1)

	async def check_channel_permissions(self, guild: discord.Guild) :
		channel = guild.get_channel(ConfigData().get_key_int_or_zero(guild.id, "approval_channel"))
		if channel is None :
			logging.warning("Mod channel is None, cannot check permissions")
			channel = find_first_accessible_text_channel(guild)
		if channel is None :
			# No approval channel and no channel the bot can post in (AGEVERIFIER-FY); the owner is the last resort.
			channel = guild.owner
		if channel is None :
			return
		embed = await self.create_permission_channels_embed(guild)
		try :
			await send_message(channel, "-# Make sure ageverifier has the right permissions to operate", embed=embed)
		except (discord.Forbidden, NoPermissionException) :
			channel = find_first_accessible_text_channel(guild)
			await send_message(channel, "-# Make sure ageverifier has the right permissions to operate", embed=embed)
		embed = await self.create_permission_roles_embed(guild)
		try :
			await send_message(channel, "-# Make sure ageverifier has the right permissions to assign roles", embed=embed)
		except (discord.Forbidden, NoPermissionException) :
			channel = find_first_accessible_text_channel(guild)
			await send_message(channel, "-# Make sure ageverifier has the right permissions to assign roles", embed=embed)

		return None

	# Shown under the embeds and on the dashboard, so both tell staff the same thing.
	CHANNEL_FIX_STEPS = [
		"Open the channel → **Edit Channel → Permissions**, add the **Ageverifier** role, and enable the missing permissions.",
		"Or grant them server-wide: **Server Settings → Roles → Ageverifier**.",
		"Re-run this check afterwards to confirm everything is green.",
	]
	ROLE_FIX_STEPS = [
		"Enable **Manage Roles** for the **Ageverifier** role in **Server Settings → Roles → Ageverifier**.",
		"Drag the **Ageverifier** role **above** every role it needs to assign — a bot can only manage roles below its own.",
		"Re-run this check afterwards to confirm everything is green.",
	]

	def audit_permissions(self, guild: discord.Guild) -> dict :
		"""The permission check as data. The Discord embeds and the dashboard API both render this."""
		channels = self.audit_channel_permissions(guild)
		roles = self.audit_role_permissions(guild)
		issue_count = sum(1 for check in channels["checks"] + roles["checks"] if check["status"] != "ok")
		if not roles["manage_roles"]["granted"] :
			issue_count += 1
		return {
			"guild"       : {"id" : str(guild.id), "name" : guild.name},
			"ok"          : issue_count == 0,
			"issue_count" : issue_count,
			"channels"    : channels,
			"roles"       : roles,
			"docs"        : {"ageverifier" : AGEVERIFIER_PERMISSIONS_DOCS, "discord" : DISCORD_PERMISSIONS_DOCS},
		}

	def audit_channel_permissions(self, guild: discord.Guild) -> dict :
		checks = []
		for key in self.channelchoices.keys() :
			check = {"key" : key, "status" : "ok", "channel_id" : None, "channel_name" : None, "missing" : []}
			try :
				channel = guild.get_channel(ConfigData().get_key_int_or_zero(guild.id, key))
				if channel is None :
					check["status"] = "not_set"
				else :
					check["channel_id"] = str(channel.id)
					check["channel_name"] = channel.name
					missing = check_missing_channel_permissions(channel, DEFAULT_CHANNEL_PERMS)
					if missing :
						check["status"] = "missing"
						check["missing"] = [describe_permission(perm) for perm in missing]
			except Exception as e :
				logging.error(e, exc_info=True)
				check["status"] = "error"
			check["message"] = self.channel_check_text(check)
			checks.append(check)
		return {
			"ok"        : all(check["status"] == "ok" for check in checks),
			"checks"    : checks,
			"fix_steps" : self.CHANNEL_FIX_STEPS,
		}

	@staticmethod
	def channel_check_text(check: dict, channel_ref: str | None = None) -> str :
		"""``channel_ref`` names the channel; the embed passes a mention, the dashboard gets #name."""
		if check["status"] == "not_set" :
			return "Not set, or the channel no longer exists — set it with `/config channels`"
		if check["status"] == "error" :
			return "Error checking permissions"
		if check["status"] == "missing" :
			channel_ref = channel_ref or f"#{check['channel_name']}"
			return f"{channel_ref} is missing: {', '.join(perm['label'] for perm in check['missing'])}"
		return "All required permissions are set"

	def audit_role_permissions(self, guild: discord.Guild) -> dict :
		top_role = guild.me.top_role
		can_manage_roles = guild.me.guild_permissions.manage_roles
		checks = [self.audit_role_key(guild, key, ConfigData().get_key_or_none(guild.id, key), top_role)
		          for key in self.rolechoices.keys()]
		for age_role in AgeRoleTransactions().get_all_guild(guild.id) :
			checks.append(self.audit_role_key(guild, "age role", age_role.role_id, top_role))
		checks = [check for check in checks if check is not None]
		return {
			"ok"           : can_manage_roles and all(check["status"] == "ok" for check in checks),
			"manage_roles" : {
				**describe_permission("manage_roles"),
				"granted" : can_manage_roles,
				"message" : "I have permission to give roles" if can_manage_roles else "I don't have permission to give roles",
			},
			"top_role"     : {"id" : str(top_role.id), "name" : top_role.name},
			"checks"       : checks,
			"fix_steps"    : self.ROLE_FIX_STEPS,
		}

	def audit_role_key(self, guild: discord.Guild, key: str, data, top_role: discord.Role) -> dict | None :
		"""Checks every role stored under one config key (or one age role) against the bot's top role."""
		check = {"key" : key, "type" : "age role" if key == "age role" else "role", "status" : "ok", "roles" : []}
		if not data :
			check["status"] = "not_set"
			check["message"] = "This key was not set"
			return check
		if isinstance(data, str | int) :
			data = [data]
		if not isinstance(data, list) :
			return None
		for role_id in data :
			entry = {"id" : str(role_id), "name" : None, "status" : "ok"}
			try :
				# Single-role keys such as approval_ping_role are cached as the raw
				# database string, and get_role only matches int keys.
				role = guild.get_role(int(role_id))
				if role is None :
					raise ValueError("Role is None")
				entry["name"] = role.name
				if role.position >= top_role.position :
					entry["status"] = "above_bot"
			except ValueError :
				entry["status"] = "not_found"
				entry["message"] = "Unable to retrieve role"
			except Exception as e :
				logging.error(e, exc_info=True)
				entry["status"] = "error"
				entry["message"] = "Error checking permissions"
			check["roles"].append(entry)

		above_bot = [entry for entry in check["roles"] if entry["status"] == "above_bot"]
		if above_bot :
			check["status"] = "above_bot"
			check["message"] = f"I don't have permission to assign roles: {', '.join(entry['name'] for entry in above_bot)}"
		elif any(entry["status"] != "ok" for entry in check["roles"]) :
			check["status"] = "error"
			check["message"] = "; ".join(f"{entry['id']}: {entry['message']}" for entry in check["roles"] if entry["status"] != "ok")
		else :
			check["message"] = "I have permission to assign this role"
		return check

	async def create_permission_channels_embed(self, guild: discord.Guild) :
		audit = self.audit_channel_permissions(guild)
		embed = discord.Embed(title="Permissions Check (channels)", color=0x00ff00 if audit["ok"] else 0xff0000)
		embed.description = f"Checking channel permissions in {guild.name}:"
		for check in audit["checks"] :
			mention = f"<#{check['channel_id']}>" if check["channel_id"] else None
			mark = "✅" if check["status"] == "ok" else "❌"
			embed.add_field(name=f"**{check['key']}**", value=f"{mark} {self.channel_check_text(check, mention)}", inline=False)
		if not audit["ok"] :
			self.add_fix_steps_field(embed, audit["fix_steps"])
		return embed

	async def create_permission_roles_embed(self, guild: discord.Guild) :
		audit = self.audit_role_permissions(guild)
		ement = discord.Embed(title="Permissions Check (roles)", color=0x00ff00 if audit["ok"] else 0xff0000)
		ement.description = f"Checking role permissions in {guild.name}:"
		mark = "✅" if audit["manage_roles"]["granted"] else "❌"
		ement.add_field(name=f"role giving permission", value=f"{mark} {audit['manage_roles']['message']}", inline=False)
		for check in audit["checks"] :
			# Leave room for the fix steps under Discord's 25 field limit.
			if len(ement.fields) > 20 :
				break
			self.add_role_check_fields(ement, check)
		if not audit["ok"] :
			self.add_fix_steps_field(ement, audit["fix_steps"])
		return ement

	@staticmethod
	def add_role_check_fields(embed: discord.Embed, check: dict) :
		key = check["key"]
		if check["status"] in ("ok", "not_set", "above_bot") :
			mark = "✅" if check["status"] == "ok" else "❌"
			embed.add_field(name=f"**{key}**", value=f"{mark} {check['message']}", inline=False)
			if check["status"] != "above_bot" :
				return
		# Roles we could not look up get their own field, so staff can see which id is stale.
		for entry in check["roles"] :
			if entry["status"] in ("not_found", "error") :
				embed.add_field(name=f"**{key} - {entry['id']}**", value=f"❌ {entry['message']}", inline=False)

	@staticmethod
	def add_fix_steps_field(embed: discord.Embed, steps: list[str]) :
		embed.add_field(
			name="How to fix",
			value="\n".join(f"{i}. {step}" for i, step in enumerate(steps, start=1)),
			inline=False,
		)
