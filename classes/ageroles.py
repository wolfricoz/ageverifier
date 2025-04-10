import discord

from classes.databaseController import ConfigData
from classes.support.discord_tools import send_message
from classes.support.queue import queue


def change_age_roles(guild: discord.Guild, user: discord.Member, age, remove = False) :
	"""Adds the age roles to the user and removes the age roles that are not in the range if remove is True."""
	roles = ConfigData().get_key(guild.id, "ADD")
	add_roles = []
	remove_roles = []
	for key, value in roles.items() :
		role = guild.get_role(key)
		if value['MIN'] <= age <= value['MAX']:
			if role not in user.roles:
				add_roles.append(role)
			continue
		if role not in user.roles :
			continue
		remove_roles.append(role)
	if len(add_roles) > 0 :
		queue().add(user.add_roles(*add_roles), priority=2 if not remove else 0)
	if remove is False:
		return
	if len(remove_roles) < 1 :
		return
	queue().add(user.remove_roles(*remove_roles), priority=0)
	mod_lobby = guild.get_channel(ConfigData().get_key_int(guild.id, "lobbymod"))
	if mod_lobby is None:
		return
	queue().add(send_message(mod_lobby, f"[AGE ROLES UPDATED] {user.mention} has been given the roles: {', '.join([role.name for role in add_roles])} and removed the roles: {', '.join([role.name for role in remove_roles])}"), priority=0)




