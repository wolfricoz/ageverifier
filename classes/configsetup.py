import logging

import discord
from discord.utils import get

from databases.controllers.ConfigData import ConfigData
from databases.controllers.ConfigTransactions import ConfigTransactions
from discord_py_utilities.messages import send_message
from classes.support.queue import Queue
from views.buttons.confirmButtons import confirmAction
from views.select.configselectroles import ConfigSelectRoles, ConfigSelectChannels
from resources.data.config_variables import rolechoices, channelchoices, messagechoices


class ConfigSetup :
	"""This class is used to setup the configuration for the bot"""
	rolechoices = rolechoices
	channelchoices = channelchoices
	messagechoices = messagechoices

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
			if key == "return" :
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

		if confirmation.confirmed is False :
			await interaction.followup.send("Setup Cancelled")
			return None
		category = get(interaction.guild.categories, name="Lobby")
		if not category :
			category: discord.CategoryChannel = await interaction.guild.create_category(name="Lobby", overwrites={
				interaction.guild.default_role : discord.PermissionOverwrite(read_messages=False),
				interaction.guild.me           : discord.PermissionOverwrite(read_messages=True)
			})
		await self.create_channels(interaction.guild, category, channelchoices, interaction)
		await self.create_roles(interaction.guild, rolechoices, interaction)
		await self.set_messages(interaction.guild, messagechoices)
		return True

	async def add_roles_to_channel(self, channel, roles) :
		for r in roles :
			await channel.set_permissions(r, read_messages=True, send_messages=True)

	async def create_channels(self, guild, category, channelchoices, interaction=None) :
		for channelkey, channelvalue in channelchoices.items() :
			channel = None
			logging.info("setting up channel: " + channelkey)
			try :
				match channelkey :
					case 'inviteinfo' :
						print("setting up invite info")
						channel = await self.create_channel(guild, category, "invite-info",
						                                    "This channel shows you additional join "
						                                    "information about the user.")

					case 'general' :
						general: discord.TextChannel = get(guild.text_channels, name="general")
						if general :
							ConfigTransactions().config_unique_add(guild.id, channelkey, general.id, overwrite=True)
							continue
						if interaction is None :
							logging.info("Automated Setup, skipping general channel")
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
					case 'lobby' :
						# This is your lobby channel, where the lobby welcome message will be posted.
						# This is also where the verification process will start; this is where new users should interact with the bot.
						# this channel should be open to everyone.
						channel = await self.create_channel(guild, category, "lobby",
						                                    "This is where the users enter your server and are welcomed.")
						# await self.add_roles_to_channel(channel, roles)
						await channel.set_permissions(guild.default_role, read_messages=True, send_messages=True)

					case 'lobbylog' :
						# This is the channel where the lobby logs will be posted.
						# This channel has to be hidden from the users; failure to do so will result in the bot leaving.
						channel = await self.create_channel(guild, category, "lobby-log",
						                                    "This is where the ages of the users are logged, this channel should never be public.")
					# await self.add_roles_to_channel(channel, roles)

					case 'lobbymod' :
						# This is where the verification approval happens.
						# This channel should be hidden from the users.
						channel = await self.create_channel(guild, category, "lobby-moderation",
						                                    "This channel is where you approve your users and receive age-verifier related information. This channel should never be public.")
					# await self.add_roles_to_channel(channel, roles)

					case 'idlog' :
						# This is where failed verification logs will be posted.
						# This channel should be hidden from the users.
						channel = await self.create_channel(guild, category, "id-check",
						                                    "This channel is where age discrepancies are flagged for ID verification. This channel should never be public.")
					# await self.add_roles_to_channel(channel, roles)

					case _ :
						continue
				try :
					ConfigTransactions().config_unique_add(guild.id, channelkey, channel.id, overwrite=True)
					return None
				except Exception as e :
					logging.error(e, exc_info=True)
					return None
			except Exception as e :
				logging.error(e, exc_info=True)
				return None
		return None

	async def create_roles(self, guild, rolechoices, interaction=None) :
		skip_roles = ['return', 'add']
		for key, value in rolechoices.items() :
			if key == "return" :
				continue
			if key in skip_roles :
				if key == "add" :
					if verified := [r for r in guild.roles if r.name.lower() == "verified"] :
						ConfigTransactions().config_unique_add(guild.id, "add", verified[0].id, overwrite=True)
						continue
					verified = get(guild.roles, name="Verified")
					if verified is None :
						verified = await guild.create_role(name="Verified", reason="Setup")
					ConfigTransactions().config_unique_add(guild.id, "add", verified.id, overwrite=True)
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
			ConfigTransactions().config_unique_add(guild.id, key, int(view.value[0]), overwrite=True)
			return None
		return None

	async def set_messages(self, guild, messagechoices) :
		for messagekey, messagevalue in messagechoices.items() :
			message_dict = {
				'lobbywelcome'   : f"Please read the rules in the rules channel and click the verify button below to get started.",
				'welcomemessage' : "Be sure to get some roles in the roles channel and if you need help be sure to ask the staff!",
			}
			ConfigTransactions().config_unique_add(guild.id, messagekey, message_dict[messagekey], overwrite=True)

	async def create_channel(self, guild, category, name, description=None) :
		channel = get(guild.text_channels, name=name)
		if not channel :
			channel = await category.create_text_channel(name=name)
		await channel.edit(topic=description)
		return channel

	async def api_auto_setup(self, guild: discord.Guild) :
		category = get(guild.categories, name="Lobby")
		if not category :
			category: discord.CategoryChannel = await guild.create_category(name="Lobby", overwrites={
				guild.default_role : discord.PermissionOverwrite(read_messages=False),
				guild.me           : discord.PermissionOverwrite(read_messages=True)
			})
		Queue().add(ConfigSetup().create_channels(guild, category, channelchoices), 2)
		Queue().add(ConfigSetup().create_roles(guild, rolechoices), 2)
		Queue().add(ConfigSetup().set_messages(guild, messagechoices), 2)
		lobby_mod = guild.get_channel(ConfigData().get_key_int(guild.id, "lobbymod"))
		Queue().add(send_message(lobby_mod, f"## Auto Setup for {guild.name} has been completed!"), 0)
		Queue().add(send_message(guild.owner, f"## Auto Setup for {guild.name} has been completed!"), 0)

	async def check_channel_permissions(self, mod_channel: discord.TextChannel, interaction: discord.Interaction = None) :
		fails = []
		for key in self.channelchoices :
			try :
				channel = ConfigData().get_key_or_none(mod_channel.guild.id, key)
				if channel is None or channel == "" :
					await send_message(mod_channel,
					                   f"{key} is not set, please set it with /config channels\n[DEBUG] {key}: {channel}")
					fails.append(key)
					continue
				try :
					channel = mod_channel.guild.get_channel(int(channel))
				except AttributeError :
					continue

				if channel is None :
					await send_message(mod_channel, f"{key} is not a valid channel, please set it with /config channels")
					fails.append(key)
					continue
				try :
					msg = await send_message(channel, "Checking permissions, if you see this I can post here!")
					await msg.delete()
				except discord.Forbidden :
					await send_message(mod_channel, f"I do not have permissions to post in {channel.name}")
					fails.append(key)
					continue
				await mod_channel.send(f"I have permissions to post in {channel.name}!")
			except Exception as e :
				logging.error(e, exc_info=True)
				fails.append(key)
		if len(fails) > 0 :
			warning = f"Failed to check permissions for: {', '.join(fails)}"
			if interaction is None :
				return await send_message(mod_channel.guild.owner, warning)
			await interaction.followup.send(warning)

			return None
		success = "All permissions are set correctly!"
		if interaction is None :
			return await send_message(mod_channel.guild.owner, success)
		await interaction.followup.send(success)
		return None
