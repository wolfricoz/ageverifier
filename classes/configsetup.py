import logging

import discord

from classes.databaseController import ConfigTransactions, ConfigData
from views.buttons.confirmButtons import confirmAction
from views.select.configselectroles import ConfigSelectRoles, ConfigSelectChannels


class configSetup:
    """This class is used to setup the configuration for the bot"""

    async def manual(self, bot, interaction: discord.Interaction, channelchoices: dict, rolechoices: dict, messagechoices: dict):
        logging.info("Manual setup started")
        await interaction.response.defer(ephemeral=True)
        for channelkey, channelvalue in channelchoices.items():
            view = ConfigSelectChannels()
            msg = await interaction.channel.send(f"Select a channel for {channelkey}: \n`{channelvalue}`", view=view)
            await view.wait()
            await msg.delete()
            try:
                if view.value == "next":
                    continue
                if view.value is None:
                    await interaction.followup.send("Setup cancelled")
                    return
            except AttributeError:
                logging.info("No value found, message was deleted")
                return
            ConfigTransactions.config_unique_add(interaction.guild.id, channelkey, int(view.value[0]), overwrite=True)
        for key, value in rolechoices.items():
            if key == "return":
                continue
            view = ConfigSelectRoles()
            msg = await interaction.channel.send(f"{key}: \n{value}", view=view)
            await view.wait()
            await msg.delete()
            try:
                if view.value == "next":
                    continue
                if view.value is None:
                    await interaction.followup.send("Setup cancelled")
                    return
            except AttributeError:
                logging.info("No value found, message was deleted")
                return
            ConfigTransactions.config_unique_add(interaction.guild.id, value, int(view.value[0]), overwrite=True)
        for messagekey, messagevalue in messagechoices.items():
            msg = await interaction.channel.send(f"Please set the message for {messagekey}\n"
                                                 f"{messagevalue}\n"
                                                 f"Type `cancel` to cancel, or `next` to go to the next message")
            result = await bot.wait_for('message', check=lambda m: m.author == interaction.user)
            if result.content.lower() == "cancel":
                await interaction.followup.send("Setup cancelled")
                return
            if result.content.lower() == "next":
                continue
            ConfigTransactions.config_unique_add(interaction.guild.id, messagekey, result.content, overwrite=True)
            await result.delete()
            await msg.delete()

    async def auto(self, interaction: discord.Interaction, channelchoices: dict, rolechoices: dict, messagechoices: dict):
        logging.info("Auto setup started")
        confirmation = confirmAction()
        await confirmation.send_message(interaction, "Are you sure you want to automatically setup the configuration for this server? You may see new channels and roles created and some configuration still needs to be done manually.")
        await confirmation.wait()

        skip_roles = ['return', 'add']
        if confirmation.confirmed is False:
            await interaction.followup.send("Purge cancelled")
            return

        for key, value in rolechoices.items():
            if key == "return":
                continue
            if key in skip_roles:
                if key == "add":
                    verified = await interaction.guild.create_role(name="Verified", reason="Setup")
                    ConfigTransactions.config_unique_add(interaction.guild.id, "add", verified.id, overwrite=True)
                    continue

                continue
            view = ConfigSelectRoles()
            msg = await interaction.channel.send(f"{key}: \n{value}", view=view)
            await view.wait()
            await msg.delete()
            try:
                if view.value == "next":
                    continue
                if view.value is None:
                    await interaction.followup.send("Setup cancelled")
                    return
            except AttributeError:
                logging.info("No value found, message was deleted")
            ConfigTransactions.config_unique_add(interaction.guild.id, key, int(view.value[0]), overwrite=True)

        roles = []
        for r in ['admin', 'mod']:
            roles.append(interaction.guild.get_role(ConfigData().get_key(interaction.guild.id, r)[0]))

        category: discord.CategoryChannel = await interaction.guild.create_category(name="Lobby", overwrites={
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.guild.me          : discord.PermissionOverwrite(read_messages=True)
        })
        await self.add_roles_to_channel(category, roles)

        for channelkey, channelvalue in channelchoices.items():
            channel = None
            logging.info("setting up channel: " + channelkey)
            match channelkey:
                case 'inviteinfo':
                    print("setting up invite info")
                    channel = await category.create_text_channel(name="invite-info")
                    await self.add_roles_to_channel(channel, roles)

                case 'general':
                    view = ConfigSelectChannels()
                    msg = await interaction.channel.send(f"Select a channel for {channelkey}: \n`{channelvalue}`", view=view)
                    await view.wait()
                    await msg.delete()
                    try:
                        if view.value == "next":
                            continue
                        if view.value is None:
                            await interaction.followup.send("Setup cancelled")
                            return
                    except AttributeError:
                        logging.info("No value found, message was deleted")
                        return
                    ConfigTransactions.config_unique_add(interaction.guild.id, channelkey, int(view.value[0]), overwrite=True)
                    continue
                # This is your general channel, where the welcome message will be posted
                case 'lobby':

                    # This is your lobby channel, where the lobby welcome message will be posted.
                    # This is also where the verification process will start; this is where new users should interact with the bot.
                    # this channel should be open to everyone.
                    channel = await category.create_text_channel(name="lobby")
                    await self.add_roles_to_channel(channel, roles)
                    await channel.set_permissions(interaction.guild.default_role, read_messages=True, send_messages=True)

                case 'lobbylog':
                    # This is the channel where the lobby logs will be posted.
                    # This channel has to be hidden from the users; failure to do so will result in the bot leaving.
                    channel = await category.create_text_channel(name="lobby-log")
                    await self.add_roles_to_channel(channel, roles)

                case 'lobbymod':
                    # This is where the verification approval happens.
                    # This channel should be hidden from the users.
                    channel = await category.create_text_channel(name="lobby-mod")
                    await self.add_roles_to_channel(channel, roles)

                case 'idlog':
                    # This is where failed verification logs will be posted.
                    # This channel should be hidden from the users.
                    channel = await category.create_text_channel(name="id-log")
                    await self.add_roles_to_channel(channel, roles)

                case _:
                    continue
            ConfigTransactions.config_unique_add(interaction.guild.id, channelkey, channel.id, overwrite=True)


        for messagekey, messagevalue in messagechoices.items():
            message_dict = {
                'lobbywelcome'  : f"Please read the rules in the rules channel and click the verify button below to get started.",
                'welcomemessage': "Be sure to get some roles in the roles channel and if you need help be sure to ask the staff!",
            }

            ConfigTransactions.config_unique_add(interaction.guild.id, messagekey, message_dict[messagekey], overwrite=True)

    async def add_roles_to_channel(self, channel, roles):
        for r in roles:
            await channel.set_permissions(r, read_messages=True, send_messages=True)
