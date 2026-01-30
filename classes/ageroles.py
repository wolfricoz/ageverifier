import logging

import discord
from discord_py_utilities.messages import send_message

from classes.support.queue import Queue
from databases.transactions.ConfigData import ConfigData


def change_age_roles(guild: discord.Guild, user: discord.Member, age, remove = False, reverify=False) :
	"""Adds the age roles to the user and removes the age roles that are not in the range if remove is True."""

	# Building the role list
	roles = ConfigData().get_key(guild.id, "VERIFICATION_ADD_ROLE", {})
	exluded_roles = []
	if remove :
		exluded_roles = ConfigData().get_key(guild.id, "auto_update_excluded_roles")
	roles = {key: value for key, value in roles.items() if key not in exluded_roles}
	logging.info(roles)
	add_roles = []
	remove_roles = []
	if isinstance(user, discord.User):
		user = guild.get_member(user.id)

	# Check which roles are applicable and which are not, then fetch them
	for key, value in roles.items() :
		if user is None:
			return
		role = guild.get_role(key)
		if value['MIN'] <= age <= value['MAX']:
			if role not in user.roles:
				add_roles.append(role)
			continue
		if role not in user.roles :
			continue
		remove_roles.append(role)
	# Apply the roles if user exists and roles exist.
	if user is None:
		logging.warning("User is none, they may have left the server.")
		return
	if len(add_roles) > 0:
		try:
			Queue().add(user.add_roles(*add_roles, reason="Verification Successful!"), priority=2 if not remove else 0)
		except Exception as e:
			logging.error(f"Failed to add roles to {user.mention} in {guild.name}: {e}", exc_info=True)
	# now handle reverification roles
	if not reverify :
		return
	logging.info("Reverification detected, adding reverification roles.")
	rev_roles = ConfigData().get_key(guild.id, "reverification_role")
	reverify_roles = []

	if isinstance(rev_roles, list):
		for role in rev_roles :
			role = guild.get_role(role)
			if not role :
				continue
			reverify_roles.append(role)
	else:
		if rev_roles is  None:
			return
		role = guild.get_role(rev_roles)
		if not role :
			return
		reverify_roles.append(role)
	if len(reverify_roles) > 0 :
		Queue().add(user.add_roles(*reverify_roles, reason="Reverification Roles Added"), priority=2)


	if not remove :
		return
	if len(remove_roles) < 1 :
		return
	Queue().add(user.remove_roles(*remove_roles), priority=0)
	mod_lobby = guild.get_channel(ConfigData().get_key_int(guild.id, "approval_channel"))
	if mod_lobby is None:
		return
	Queue().add(send_message(mod_lobby, f"[AGE ROLES UPDATED] {user.mention} has been given the roles: {', '.join([role.name for role in add_roles])} and removed the roles: {', '.join([role.name for role in remove_roles])}"), priority=0)








