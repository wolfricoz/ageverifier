
import logging
import os

import aiohttp
from dotenv import load_dotenv

load_dotenv()

class BanWatch :
	url = os.getenv("BANWATCH_URL")
	auth_token = os.getenv("BANWATCH_TOKEN")

	def __init__(self) :
		# We don't initialize the session here to avoid attaching it
		# to the wrong event loop during startup.
		pass

	def urlbuilder(self, path) :
		# Stripping leading slashes to prevent double slashes in the URL
		return f"{self.url}/{path}"

	async def fetchBanCount(self, user_id) :
		path = f"bans/count/{user_id}"
		target_url = self.urlbuilder(path)

		headers = {
			"X-Auth-Token" : self.auth_token,
			"Content-Type" : "application/json"
		}

		try :
			# Using a context manager for the session is safer for one-off calls,
			# though creating a persistent session is better for high-frequency bots.
			async with aiohttp.ClientSession() as session :
				async with session.get(target_url, headers=headers) as response :
					if response.status != 200 :
						logging.error(f"BanWatch returned {response.status}: {response.reason}")
						return None

					data = await response.json()

					if isinstance(data, str) :
						import json
						data = json.loads(data)
					# Ensure 'bans' exists and is greater than 0
					bans = data.get('bans')
					return bans if isinstance(bans, int) and bans > 0 else None

		except Exception as e :
			logging.error(f"Could not fetch Ban Count: {e}")
			return None