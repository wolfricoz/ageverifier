import logging

import discord
from discord_py_utilities.messages import send_message

from databases.controllers.ConfigData import ConfigData
from classes.support.queue import Queue


def change_age_roles(guild: discord.Guild, user: discord.Member, age, remove = False) :
	"""Adds the age roles to the user and removes the age roles that are not in the range if remove is True."""
	roles = ConfigData().get_key(guild.id, "ADD")
	exluded_roles = []
	if remove :
		exluded_roles = ConfigData().get_key(guild.id, "EXCLUDE")
	roles = {key: value for key, value in roles.items() if key not in exluded_roles}
	logging.info(roles)
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

	if user is None:
		logging.warning("User is none, they may have left the server.")
	if len(add_roles) > 0:
		Queue().add(user.add_roles(*add_roles), priority=2 if not remove else 0)
	if not remove :
		return
	if len(remove_roles) < 1 :
		return
	Queue().add(user.remove_roles(*remove_roles), priority=0)
	mod_lobby = guild.get_channel(ConfigData().get_key_int(guild.id, "lobbymod"))
	if mod_lobby is None:
		return
	Queue().add(send_message(mod_lobby, f"[AGE ROLES UPDATED] {user.mention} has been given the roles: {', '.join([role.name for role in add_roles])} and removed the roles: {', '.join([role.name for role in remove_roles])}"), priority=0)




