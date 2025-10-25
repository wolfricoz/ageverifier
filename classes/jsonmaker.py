import datetime
import json
import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

import pytz

# makes dir for ban logging
config_path = "settings/config.json"
# Data to be written


class Configer(ABC):
	@staticmethod
	@abstractmethod
	async def create_bot_config() :
		"""Creates the general config"""
		if not os.path.isdir("settings") :
			os.mkdir("settings")
		dictionary = {
			"blacklist" : [],
			"checklist" : [

			],
		}
		json_object = json.dumps(dictionary, indent=4)
		if os.path.exists(config_path) :
			with open(config_path) as f :
				data = json.load(f)
				dictionary = {
					"user_blacklist" : data.get("user_blacklist", []),
					"blacklist"      : data.get("blacklist", []),
					"checklist"      : data.get("checklist", [])
				}
			with open(config_path, "w") as f :
				json.dump(dictionary, f, indent=4)
			return
		with open(config_path, "w") as outfile :
			outfile.write(json_object)
			logging.info(f"universal config created")

	# blacklist starts here

	@staticmethod
	@abstractmethod
	async def add_to_blacklist(guildid) :
		"""Adds a server to the blacklist"""
		if os.path.exists(config_path) :
			with open(config_path) as f :
				data = json.load(f)
				if guildid in data.get("blacklist", []):
					return
				data["blacklist"].append(guildid)
			with open(config_path, 'w') as f :
				json.dump(data, f, indent=4)
				logging.info(f"{guildid} added to blacklist")
		else :
			logging.warning("No blacklist found")

	@staticmethod
	@abstractmethod
	async def remove_from_blacklist(guildid) :
		"""Removes a server from the blacklist"""
		if os.path.exists(config_path) :
			with open(config_path) as f :
				data = json.load(f)
				data["blacklist"].remove(guildid)
			with open(config_path, 'w') as f :
				json.dump(data, f, indent=4)
				logging.info(f"{guildid} removed from blacklist")
		else :
			logging.warning("No blacklist found")

	@staticmethod
	@abstractmethod
	async def is_blacklisted(guildid) :
		"""Checks if a server is blacklisted"""
		if os.path.exists(config_path) :
			with open(config_path) as f :
				data = json.load(f)
				if guildid in data["blacklist"] :
					return True

	# user blacklist starts here
	@staticmethod
	@abstractmethod
	async def add_to_user_blacklist(userid) :
		"""Adds a user to the user blacklist"""
		if os.path.exists(config_path) :
			with open(config_path) as f :
				data = json.load(f)
				data["user_blacklist"].append(userid)
			with open(config_path, 'w') as f :
				json.dump(data, f, indent=4)
				logging.info(f"{userid} added to user blacklist")
		else :
			logging.warning("No blacklist found")

	@staticmethod
	@abstractmethod
	async def remove_from_user_blacklist(userid) :
		"""Removes a user from the user blacklist"""
		if os.path.exists(config_path) :
			with open(config_path) as f :
				data = json.load(f)
				data["user_blacklist"].remove(userid)
			with open(config_path, 'w') as f :
				json.dump(data, f, indent=4)
				logging.info(f"{userid} removed from user blacklist")
		else :
			logging.warning("No blacklist found")

	@staticmethod
	@abstractmethod
	async def is_user_blacklisted(userid) :
		"""Checks if a user is blacklisted"""
		if os.path.exists(config_path) :
			with open(config_path) as f :
				data = json.load(f)
				if userid in data["user_blacklist"] :
					return True


# noinspection PyMethodParameters
class BanLogger :
	def create(userid) :
		"""Creates the ban log, which is checked by the bot"""
		banjson = {
			"uid"  : userid,
			"bans" : {
			},
		}
		with open(f'../bans/{userid}.json', 'w') as f :
			json.dump(banjson, f, indent=4)

	def add(userid, guild, reason) :
		ban = {"reason" : reason}
		with open(f'../bans/{userid}.json', 'r+') as f :
			data = json.load(f)
			data['bans'][guild] = ban
			print(data)
		with open(f'../bans/{userid}.json', 'w') as f :
			json.dump(data, f, indent=4)

	def read(userid) :
		with open(f'../bans/{userid}.json', 'r+') as f :
			data = json.load(f)
			for d, x in data['bans'].items() :
				print(f"{d}: {x['reason']}")

	def check(userid) :
		if os.path.exists(f'../bans/{userid}.json') :
			with open(f'../bans/{userid}.json', 'r+') as f :
				data = json.load(f)
				if len(data['bans'].items()) == 0 :
					print("user not banned")
				else :
					BanLogger.read(userid)
		else :
			print("user not banned")


class Cooldown :
	def add(self, userid, channel, time) :

		with open(f'./users/{userid}.json', 'r+') as f :
			data = json.load(f)
			data['cooldowns'][channel] = time.strftime('%x %X')
		with open(f'./users/{userid}.json', 'w') as f :
			json.dump(data, f, indent=4)

	def check(self, userid, channel, time) :
		with open(f'./users/{userid}.json', 'r+') as f :
			tz = pytz.timezone('US/Eastern')
			data = json.load(f)
			now = datetime.now(tz)

			if str(channel) in data['cooldowns'] :
				print("cooldown found")
				print(data['cooldowns'][str(channel)])
				cooldown = "".join(data['cooldowns'][str(channel)])
				if now.strftime('%x %X') > cooldown :
					print("Can post")
					return True
				else :
					print("Can't post")
					return False
			else :
				Cooldown.add(self, userid, channel, time)
				return True

	async def notify(self, userid, channel, modchannel, message) :
		with open(f'./users/{userid}.json', 'r+') as f :
			tz = pytz.timezone('US/Eastern')
			data = json.load(f)
			now = datetime.now(tz)

			if str(channel) in data['cooldowns'] :
				cooldown = "".join(data['cooldowns'][str(channel)])

				await modchannel.send(f"{message.author.mention} has posted too early in {message.channel.mention}. \n"
				                      f"Last post: {cooldown} in <#{str(channel)}>")
	@staticmethod
	@abstractmethod
	async def create_bot_config() :
		"""Creates the general config"""
		if not os.path.isdir("settings") :
			os.mkdir("settings")
		dictionary = {
			"blacklist" : [],
			"checklist" : [

			],
		}
		json_object = json.dumps(dictionary, indent=4)
		if os.path.exists(config_path) :
			with open(config_path) as f :
				data = json.load(f)
				dictionary = {
					"user_blacklist" : data.get("user_blacklist", []),
					"blacklist"      : data.get("blacklist", []),
					"checklist"      : data.get("checklist", [])
				}
			with open(config_path, "w") as f :
				json.dump(dictionary, f, indent=4)
			return
		with open(config_path, "w") as outfile :
			outfile.write(json_object)
			logging.info(f"universal config created")

	# blacklist starts here

	@staticmethod
	@abstractmethod
	async def add_to_blacklist(guildid) :
		"""Adds a server to the blacklist"""
		if os.path.exists(config_path) :
			with open(config_path) as f :
				data = json.load(f)
				data["blacklist"].append(guildid)
			with open(config_path, 'w') as f :
				json.dump(data, f, indent=4)
				logging.info(f"{guildid} added to blacklist")
		else :
			logging.warning("No blacklist found")

	@staticmethod
	@abstractmethod
	async def remove_from_blacklist(guildid) :
		"""Removes a server from the blacklist"""
		if os.path.exists(config_path) :
			with open(config_path) as f :
				data = json.load(f)
				data["blacklist"].remove(guildid)
			with open(config_path, 'w') as f :
				json.dump(data, f, indent=4)
				logging.info(f"{guildid} removed from blacklist")
		else :
			logging.warning("No blacklist found")

	@staticmethod
	@abstractmethod
	async def is_blacklisted(guildid) :
		"""Checks if a server is blacklisted"""
		if os.path.exists(config_path) :
			with open(config_path) as f :
				data = json.load(f)
				if guildid in data["blacklist"] :
					return True

	# user blacklist starts here
	@staticmethod
	@abstractmethod
	async def add_to_user_blacklist(userid) :
		"""Adds a user to the user blacklist"""
		if os.path.exists(config_path) :
			with open(config_path) as f :
				data = json.load(f)
				data["user_blacklist"].append(userid)
			with open(config_path, 'w') as f :
				json.dump(data, f, indent=4)
				logging.info(f"{userid} added to user blacklist")
		else :
			logging.warning("No blacklist found")

	@staticmethod
	@abstractmethod
	async def remove_from_user_blacklist(userid) :
		"""Removes a user from the user blacklist"""
		if os.path.exists(config_path) :
			with open(config_path) as f :
				data = json.load(f)
				data["user_blacklist"].remove(userid)
			with open(config_path, 'w') as f :
				json.dump(data, f, indent=4)
				logging.info(f"{userid} removed from user blacklist")
		else :
			logging.warning("No blacklist found")

	@staticmethod
	@abstractmethod
	async def is_user_blacklisted(userid) :
		"""Checks if a user is blacklisted"""
		if os.path.exists(config_path) :
			with open(config_path) as f :
				data = json.load(f)
				if userid in data["user_blacklist"] :
					return True

class Updater :
	async def update(self) :
		count = 0
		for x in os.listdir('../rmrbot/users') :
			print(x)
			with open(f'./users/{x}', 'r+') as f :
				data = json.load(f)
				dictionary = {
					"Name"      : data['Name'],
					"warnings"  : data['warnings'],
					"cooldowns" : {
					},
				}
			with open(f'./users/{x}', 'w') as f :
				json.dump(dictionary, f, indent=4)
			count += 1
		print(f"updated: {count}")


# noinspection PyMethodParameters,PyShadowingBuiltins
class Datechecker :
	def datecheck(input, channel, timedelt) :
		now = datetime.now()
		later = now + timedelta(days=timedelt)
		Cooldown().add(input, channel, later)
		Cooldown().check(input, channel, timedelt)
		print(now)
		print(later)
		if now.strftime('%x %X') > str(Cooldown().check(input, channel, timedelt)) :
			print("time has passed")
		else :
			print("on cooldown")


# noinspection PyMethodParameters
class guildconfiger(ABC) :
	@abstractmethod
	async def create(guildid, guildname) :
		try :
			os.mkdir("../rmrbot/jsons")
		except :
			pass
		"Creates the config"
		dictionary = {
			"Name"         : guildname,
			"addrole"      : [],
			"remrole"      : [],
			"welcomeusers" : True,
			"welcome"      : "This can be changed with /config welcome",
			"waitingrole"  : [],
			"forums"       : []
		}
		json_object = json.dumps(dictionary, indent=4)
		if os.path.exists(f"jsons/{guildid}.json") :
			with open(f"../rmrbot/jsons/template.json", "w") as outfile :
				outfile.write(json_object)
		else :
			with open(f"jsons/{guildid}.json", "w") as outfile :
				outfile.write(json_object)
				print(f"config created for {guildid}")

	@abstractmethod
	async def edit_string(guildid, newstr, key) :
		if os.path.exists(f"jsons/{guildid}.json") :
			with open(f"jsons/{guildid}.json") as f :
				data = json.load(f)
				data[key] = newstr
			with open(f"jsons/{guildid}.json", 'w') as f :
				json.dump(data, f, indent=4)

	@abstractmethod
	async def addrole(guildid, interaction, roleid, key) :
		if os.path.exists(f"jsons/{guildid}.json") :
			with open(f"jsons/{guildid}.json") as f :
				data = json.load(f)
				for x in data[key] :
					if x == roleid :
						await interaction.followup.send("Failed to add role! Role already in config")
						break
				else :
					data[key].append(roleid)
					await interaction.followup.send(f"Role added to {key}")
			with open(f"jsons/{guildid}.json", 'w') as f :
				json.dump(data, f, indent=4)

	@staticmethod
	@abstractmethod
	async def remrole(guildid, roleid, key) :
		if os.path.exists(f"jsons/{guildid}.json") :
			with open(f"jsons/{guildid}.json") as f :
				data = json.load(f)
				data[key].remove(roleid)
			with open(f"jsons/{guildid}.json", 'w') as f :
				json.dump(data, f, indent=4)

	@staticmethod
	@abstractmethod
	async def addforum(guildid, interaction, roleid, key) :
		if os.path.exists(f"jsons/{guildid}.json") :
			with open(f"jsons/{guildid}.json") as f :
				data = json.load(f)
				for x in data[key] :
					if x == roleid :
						await interaction.followup.send("Failed to add forum! forum already in config")
						break
				else :
					data[key].append(roleid)
					await interaction.followup.send(f"forum added to {key}")
			with open(f"jsons/{guildid}.json", 'w') as f :
				json.dump(data, f, indent=4)

	@staticmethod
	@abstractmethod
	async def remforum(guildid: int, channelid: int, key) :
		if os.path.exists(f"jsons/{guildid}.json") :
			with open(f"jsons/{guildid}.json") as f :
				data = json.load(f)
				data[key].remove(channelid)
			with open(f"jsons/{guildid}.json", 'w') as f :
				json.dump(data, f, indent=4)

	@staticmethod
	@abstractmethod
	async def welcome(guildid, interaction, key, welcome) :
		if os.path.exists(f"jsons/{guildid}.json") :
			with open(f"jsons/{guildid}.json") as f :
				data = json.load(f)
				data[key] = welcome
			with open(f"jsons/{guildid}.json", 'w') as f :
				json.dump(data, f, indent=4)
			await interaction.followup.send(f"welcome updated to '{welcome}'")

	@staticmethod
	@abstractmethod
	async def roulette(guildid: int, channelid: int, key) :
		if os.path.exists(f"jsons/{guildid}.json") :
			with open(f"jsons/{guildid}.json") as f :
				data = json.load(f)
				data[key] = channelid
			with open(f"jsons/{guildid}.json", 'w') as f :
				json.dump(data, f, indent=4)

	@staticmethod
	@abstractmethod
	async def updateconfig(guildid) :
		with open(f'jsons/{guildid}.json', 'r+') as file :
			data = json.load(file)
			newdictionary = {
				"Name"         : data.get('Name', None),
				"addrole"      : data.get('addrole', []),
				"remrole"      : data.get('remrole', []),
				"welcomeusers" : data.get("welcomeusers", False),
				"welcome"      : data.get('welcome', "This can be changed with /config welcome"),
				"waitingrole"  : data.get('waitingrole', []),
				"forums"       : data.get('forums', []),
				"roulette"     : data.get('roulette', None),
				"reminder"     : data.get('reminder', "")
			}
		with open(f'jsons/{guildid}.json', 'w') as f :
			json.dump(newdictionary, f, indent=4)

	@staticmethod
	@abstractmethod
	async def viewconfig(interaction, guildid) :
		if os.path.exists(f"jsons/{guildid}.json") :
			with open(f"jsons/{guildid}.json") as f :
				data = json.load(f)
				vdict = f"""
Name: {data['Name']}
addrole: {data['addrole']}
remrole: {data['remrole']}
welcomeusers: {data['welcomeusers']},
welcome: {data['welcome']}
waitingrole: {data['waitingrole']}
                """
				return vdict


