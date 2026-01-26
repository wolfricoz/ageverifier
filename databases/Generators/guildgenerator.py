import random

from databases.current import Servers
from databases.transactions.ServerTransactions import ServerTransactions
from databases.transactions.UserTransactions import UserTransactions


class guildgenerator :

	def create(self, amount = 1) -> Servers | list[Servers]:
		count = 0
		class owner():


			id = UserTransactions().add_user_empty(random.randint(100000000000000000, 900000000000000000)).uid
			name = "OwnerName"


		if amount < 2:
			guild_id = random.randint(400000000000000000, 900000000000000000)
			return ServerTransactions().add(guild_id, owner=owner(), active=True)
		servers = []
		while count < amount :
			guild_id = random.randint(400000000000000000, 900000000000000000)
			servers.append(ServerTransactions().add(guild_id, active=True))
			count += 1
		return servers