import logging

import discord
from discord.utils import get
from discord_py_utilities.exceptions import NoPermissionException
from discord_py_utilities.messages import send_message
from discord_py_utilities.permissions import check_missing_channel_permissions, find_first_accessible_text_channel

from classes.config.utils import ConfigUtils
from classes.support.queue import Queue
from databases.transactions.AgeRoleTransactions import AgeRoleTransactions
from databases.transactions.ConfigData import ConfigData
from databases.transactions.ConfigTransactions import ConfigTransactions
from resources.data.config_variables import available_toggles, channelchoices, messagechoices, rolechoices
from views.buttons.confirmButtons import confirmAction
from views.select.configselectroles import ConfigSelectChannels, ConfigSelectRoles


class ConfigSetup :
	"""This class is used to setup the configuration for the bot"""
	rolechoices = rolechoices
	channelchoices = channelchoices
	messagechoices = messagechoices
	available_toggles = available_toggles
	changes = {}

	async def manual(self, bot, interaction: discord.Interaction, channelchoices: dict, rolechoices: dict,
	                 messagechoices: dict) :
		logging.info("Manual setup started")
		await interaction.response.defer(ephemeral=True)
		for channelkey, channelvalue in channelchoices.items() :
			view = ConfigSelectChannels()
			msg = await interaction.channel.send(f"Select a channel for {channelkey}: \n`{channelvalue}`", view=view)
			await view.wait()
			await msg.delete()
			try :
				if view.value == "next" :
					continue
				if view.value is None :
					await interaction.followup.send("Setup cancelled")
					return
			except AttributeError :
				logging.info("No value found, message was deleted")
				return
			ConfigTransactions().config_unique_add(interaction.guild.id, channelkey, int(view.value[0]), overwrite=True)
		for key, value in rolechoices.items() :
			if key == "return_remove_role" :
				continue
			view = ConfigSelectRoles()
			msg = await interaction.channel.send(f"{key}: \n{value}", view=view)
			await view.wait()
			await msg.delete()
			try :
				if view.value == "next" :
					continue
				if view.value is None :
					await interaction.followup.send("Setup cancelled")
					return
			except AttributeError :
				logging.info("No value found, message was deleted")
				return
			ConfigTransactions().config_unique_add(interaction.guild.id, value, int(view.value[0]), overwrite=True)
		for messagekey, messagevalue in messagechoices.items() :
			msg = await interaction.channel.send(f"Please set the message for {messagekey}\n"
			                                     f"{messagevalue}\n"
			                                     f"Type `cancel` to cancel, or `next` to go to the next message")
			result = await bot.wait_for('message', check=lambda m : m.author == interaction.user)
			if result.content.lower() == "cancel" :
				await interaction.followup.send("Setup cancelled")
				return
			if result.content.lower() == "next" :
				continue
			ConfigTransactions().config_unique_add(interaction.guild.id, messagekey, result.content, overwrite=True)
			await result.delete()
			await msg.delete()

	async def auto(self, interaction: discord.Interaction, channelchoices: dict, rolechoices: dict,
	               messagechoices: dict) :
		logging.info("Auto setup started")
		confirmation = confirmAction()
		await confirmation.send_message(interaction,
		                                "Are you sure you want to automatically setup the configuration for this server? You may see new channels and roles created and some configuration still needs to be done manually.")
		await confirmation.wait()

		if not confirmation.confirmed :
			await interaction.followup.send("Setup Cancelled")
			return None
		category = get(interaction.guild.categories, name="Lobby")
		if not category :
			category: discord.CategoryChannel = await interaction.guild.create_category(name="Lobby", overwrites={
				interaction.guild.default_role : discord.PermissionOverwrite(read_messages=False),
				interaction.guild.me           : discord.PermissionOverwrite(read_messages=True)
			})
		await self.create_channels(interaction.guild, category, interaction)
		await self.create_roles(interaction.guild, rolechoices, interaction)
		await self.set_messages(interaction.guild, messagechoices)
		Queue().add(ConfigUtils.log_change(interaction.guild, self.changes, user_name=interaction.user.name), 1)
		return True

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
							ConfigTransactions().config_unique_add(guild.id, channelkey, verification_completed_channel.id,
							                                       overwrite=True)
							continue
						if interaction is None :
							logging.info("Automated Setup, skipping verification_completed_channel channel")
							continue
						view = ConfigSelectChannels()
						msg = await interaction.channel.send(f"Select a channel for {channelkey}: \n`{channelvalue}`", view=view)
						await view.wait()
						await msg.delete()
						try :
							if view.value == "next" :
								continue
							if view.value is None :
								await interaction.followup.send("Setup cancelled")
								return False
						except AttributeError :
							logging.info("No value found, message was deleted")
							return False
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

				try :
					self.changes[channelkey] = channel.id
					ConfigTransactions().config_unique_add(guild.id, channelkey, channel.id, overwrite=True)
					continue
				except Exception as e :
					logging.error(e, exc_info=True)
					continue
			except Exception as e :
				logging.error(e, exc_info=True)
				continue
		return True

	async def create_roles(self, guild, rolechoices, interaction=None) :
		skip_roles = ["return_remove_role", "VERIFICATION_ADD_ROLE"]
		for key, value in rolechoices.items() :
			if key == "return_remove_role" :
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
			await msg.delete()
			try :
				if view.value == "next" :
					continue
				if view.value is None :
					await interaction.followup.send("Setup cancelled")
					return False
			except AttributeError :
				logging.info("No value found, message was deleted")
			self.changes[key] = int(view.value[0])
			ConfigTransactions().config_unique_add(guild.id, key, int(view.value[0]), overwrite=True)
			return None
		return None

	async def set_messages(self, guild, messagechoices) :
		for messagekey, messagevalue in messagechoices.items() :
			message_dict = {
				'"server_join_message"'          : f"Please read the rules in the rules channel and click the verify button below to get started.",
				'verification_completed_message' : "Be sure to get some roles in the roles channel and if you need help be sure to ask the staff!",
			}
			self.changes[messagekey] = messagevalue
			ConfigTransactions().config_unique_add(guild.id, messagekey, message_dict[messagekey], overwrite=True)

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
		Queue().add(ConfigSetup().create_channels(guild, category), 2)
		Queue().add(ConfigSetup().create_roles(guild, rolechoices), 2)
		Queue().add(ConfigSetup().set_messages(guild, messagechoices), 2)
		lobby_mod = guild.get_channel(ConfigData().get_key_int(guild.id, "approval_channel"))
		Queue().add(send_message(lobby_mod, f"## Auto Setup for {guild.name} has been completed!"), 0)
		Queue().add(send_message(guild.owner, f"## Auto Setup for {guild.name} has been completed!"), 0)
		Queue().add(ConfigUtils.log_change(guild, self.changes, user_name="Dashboard"), 1)

	async def check_channel_permissions(self, guild: discord.Guild) :
		channel = guild.get_channel(ConfigData().get_key_int_or_zero(guild.id, "approval_channel"))
		if channel is None :
			logging.warning("Mod channel is None, cannot check permissions")
			channel = find_first_accessible_text_channel(guild)
		embed = await self.create_permission_channels_embed(channel.guild)
		try :
			await send_message(channel, "-# Make sure ageverifier has the right permissions to operate", embed=embed)
		except discord.Forbidden or NoPermissionException :
			channel = find_first_accessible_text_channel(guild)
			await send_message(channel, "-# Make sure ageverifier has the right permissions to operate", embed=embed)
		embed = await self.create_permission_roles_embed(channel.guild)
		try :
			await send_message(channel, "-# Make sure ageverifier has the right permissions to assign roles", embed=embed)
		except discord.Forbidden or NoPermissionException :
			channel = find_first_accessible_text_channel(guild)
			await send_message(channel, "-# Make sure ageverifier has the right permissions to assign roles", embed=embed)

		return None

	async def create_permission_channels_embed(self, guild: discord.Guild) :
		embed = discord.Embed(title="Permissions Check (channels)", color=0x00ff00)
		embed.description = f"Checking channel permissions in {guild.name}:"

		for key in self.channelchoices.keys() :
			try :
				channel = guild.get_channel(ConfigData().get_key_int_or_zero(guild.id, key))
				if channel is None :
					embed.add_field(name=f"**{key}**", value=f"❌ This key was not set or channel not found", inline=False)
					continue
				missing = check_missing_channel_permissions(channel,
				                                            ['view_channel', 'send_messages', 'embed_links', 'attach_files'])
				if len(missing) > 0 :
					embed.add_field(name=f"**{key}**", value=f"❌ Missing permissions: {', '.join(missing)}", inline=False)
					continue
				embed.add_field(name=f"**{key}**", value=f"✅ All required permissions are set", inline=False)

			except Exception as e :
				logging.error(e, exc_info=True)
				embed.add_field(name=f"**{key}**", value=f"❌ Error checking permissions", inline=False)
		return embed

	async def create_permission_roles_embed(self, guild: discord.Guild) :
		ement = discord.Embed(title="Permissions Check (roles)", color=0x00ff00)
		ement.description = f"Checking role permissions in {guild.name}:"
		top_role = guild.me.top_role
		ement.add_field(name=f"role giving permission",
		                value="✅ I have permission to give roles" if guild.me.guild_permissions.manage_roles else "❌ I don't have permission to give roles",
		                inline=False)
		for key in self.rolechoices.keys() :
			await self.process_roles(ement, guild, key, top_role)
		ageroles = AgeRoleTransactions().get_all(guild.id)
		for age_role in ageroles :
			await self.process_roles(ement, guild, str(age_role.role_id), top_role, type="age role", value=age_role.role_id)
		return ement


	async def process_roles(self, ement, guild, key, top_role, type = "role", value = None) :
		logging.info(key)
		if len(ement.fields) > 20 :
			return
		if type == "role" :
			data = ConfigData().get_key_or_none(guild.id, key)
		else :
			key = "age role"
			data = value
		if not data  :
			ement.add_field(name=f"**{key}**", value=f"❌ This key was not set", inline=False)
			return
		if isinstance(data, str | int):
			data = [data]
		if isinstance(data, list) and len(data) > 0 :
			fail = []
			for role_id in data :
				try :
					role = guild.get_role(role_id)
					if not await self.check_role_permissions(role, top_role) :
						fail.append(role_id)
						continue
				except ValueError :
					ement.add_field(name=f"**{key} - {role_id}**", value=f"❌ Unable to retrieve role", inline=False)
					continue
				except Exception as e :
					logging.error(e, exc_info=True)
					ement.add_field(name=f"**{key} - {role_id}**", value=f"❌ Error checking permissions", inline=False)
					continue
			await self.add_role_field(ement, key, len(fail) < 1, failed=fail)
			return


	async def check_role_permissions(self, role: discord.Role, top_role: discord.Role) :
		if role is None :
			raise ValueError("Role is None")
		if role.position >= top_role.position :
			return False
		return True

	async def add_role_field(self, embed, key, status: bool, failed: list = None):

		if failed and len(failed) > 0 :
			embed.add_field(name=f"**{key}**", value=f"❌ I don't have permission to assign roles: {', '.join(failed)}",
			                inline=False)
			return
		if not status :
			embed.add_field(name=f"**{key}**", value=f"❌ I don't have permission to assign this role" ,
			                inline=False)
			return
		embed.add_field(name=f"**{key}**", value=f"✅ I have permission to assign this role", inline=False)

