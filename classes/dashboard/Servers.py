import base64
import logging
import os

from databases.controllers.ServerTransactions import ServerTransactions
from databases.current import Servers as dbServers
import requests


class Servers:
	ip_address = os.getenv('DASHBOARD_URL')
	key = os.getenv('DASHBOARD_KEY')
	secret = os.getenv('DASHBOARD_SECRET')


	async def update_server(self, guild: dbServers):
		path = "/api/server/create"
		url = f"{self.ip_address}{path}"
		encoded = base64.b64encode(f"{self.key}:{self.secret}".encode('ascii')).decode()

		headers = {
			"Authorization": f"basic {encoded}",
			"Content-Type": "application/json"
		}
		logging.info(f"headers: {headers}")
		if guild.guild is None:
			return

		data = {
			"id": guild.guild,
			"ageverifier": guild.active,
			"name": guild.name,
			"owner": guild.owner,
			"owner_id": guild.owner_id,
			"member_count": guild.member_count,
			"invite": guild.invite
		}

		result = requests.post(url, headers=headers, json=data)
		if result.status_code != 200:
			logging.info(f"Server {guild.guild} could not be updated: {result.status_code}: {result.text}")

			# logging.info(f"Variables:\npath: {path}\nurl: {url}\nheaders: {headers}, key: {self.key}\nsecret: {self.secret}")
			return None
		result = result.json()
		ServerTransactions().update(guild.guild, premium=result.get('premium', None) )

		logging.info(f"Server {guild.guild} updated successfully: {result}")



		logging.info(f"Server {guild.guild} updated")

