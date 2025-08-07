import random

from databases.controllers.ServerTransactions import ServerTransactions
from databases.current import Servers


class guildgenerator :

	def create(self, amount = 1) -> Servers | list[Servers]:
		count = 0

		if amount < 2:
			guild_id = random.randint(400000000000000000, 900000000000000000)
			return ServerTransactions().add(guild_id, active=True)
		servers = []
		while count < amount :
			guild_id = random.randint(400000000000000000, 900000000000000000)
			servers.append(ServerTransactions().add(guild_id, active=True))
			count += 1
		return servers