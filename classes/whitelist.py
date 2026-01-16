import json
import logging
import os

from discord_py_utilities.messages import send_response

from classes import permissions

whitelist_path = 'whitelist.json'


def create_whitelist(guilds) :
	"""
	This function sets up the initial whitelist file.
	It's a developer tool used to create a `whitelist.json` file if one doesn't already exist, populating it with the IDs of all guilds the bot is currently in.
	This is typically only run once during the bot's initial setup.
	"""
	if os.path.exists(whitelist_path) :
		return
	whitelist_date = {
		"whitelist" : []
	}
	for guild in guilds :
		whitelist_date["whitelist"].append(guild.id)
	with open(whitelist_path, 'w') as f :
		json.dump(whitelist_date, f)


def check_whitelist(server_id) :
	"""
	Checks if a given server (guild) is on the whitelist.
	This function reads the `whitelist.json` file and returns `True` if the server's ID is found, and `False` otherwise.
	It's used to restrict access to certain features or commands.
	"""
	with open(whitelist_path, 'r') as f :
		whitelist = json.load(f)
	if server_id in whitelist["whitelist"] :
		return True
	else :
		return False


def add_to_whitelist(server_id) :
	"""
	Adds a server to the whitelist.
	This is a developer function that takes a server ID and adds it to the `whitelist.json` file, granting it access to whitelisted features.
	"""
	server_id = int(server_id)
	with open('whitelist.json', 'r') as f :
		whitelist = json.load(f)
	whitelist["whitelist"].append(server_id)
	with open(whitelist_path, 'w') as f :
		json.dump(whitelist, f)


def remove_from_whitelist(server_id) :
	"""
	Removes a server from the whitelist.
	This developer function takes a server ID and removes it from the `whitelist.json` file, revoking its access to whitelisted features.
	"""
	server_id = int(server_id)
	with open('whitelist.json', 'r') as f :
		whitelist = json.load(f)
	whitelist["whitelist"].remove(server_id)
	with open(whitelist_path, 'w') as f :
		json.dump(whitelist, f)

async def whitelist( interaction) :
	"""
	A check to see if a command can be used in the server.
	This function is used within commands to verify if the server is whitelisted. If the server is not on the whitelist and the user is not a bot developer, it sends a message explaining the restriction and returns `True`.
	If the server is whitelisted, it returns `False`, allowing the command to proceed.
	"""
	if not check_whitelist(interaction.guild.id) and not permissions.check_dev(interaction.user.id) :
		logging.info('not whitelisted')
		await send_response(interaction,
		                    f"[NOT_WHITELISTED] This command is limited to whitelisted servers. Please join our [support server]({os.getenv('INVITE')}) and open a ticket to edit or send a message to `ricostryker`")
		return True
	logging.info('whitelisted')
	return False
