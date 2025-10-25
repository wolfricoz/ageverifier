import json
import logging
import os
import requests


class BanWatch :
	url = os.getenv("BANWATCH_URL")

	def __init__(self):
		pass

	def urlbuilder(self, path):
		return f"{self.url}/{path}"


	async def fetchBanCount(self, user_id):
		path = f"/bans/count/{user_id}"
		try:
			response = requests.get(self.urlbuilder(path))
		except Exception as e:
			logging.info("Could not fetch Ban Count")
			return None
		if response.status_code != 200:
			logging.info(f"BanWatch returned {response.status_code}")
			return None
		data =json.loads(response.json())
		return data['bans'] if 'bans' in data and data['bans'] > 0 else None