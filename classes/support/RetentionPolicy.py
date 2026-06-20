import logging

from databases.transactions.ButtonTransactions import LobbyDataTransactions
from databases.transactions.HistoryTransactions import JoinHistoryTransactions
from databases.transactions.UserTransactions import UserTransactions
from databases.transactions.WebsiteDataTransactions import WebsiteDataTransactions


def enforce_data_retention_policy() :
	UserTransactions().add_user_empty(1)
	user = UserTransactions().get_user(1)
	logging.info("loaded anonimous user")
	# We anonymize the join history transactions to keep our statistics without linking it to users
	result = JoinHistoryTransactions().anonymize_data(user.uid)
	logging.info(f"Anonymized {result.rowcount} Join History Transactions")
	# We don't make statistics of this table, so we clean it up for space.
	result = WebsiteDataTransactions().clean_table()
	logging.info(f"Deleted {result.rowcount} Website Data Transactions")
	# We don't make statistics of this table, so we clean it up for space. This one grows fast otherwise.
	result = LobbyDataTransactions().clean_table()
	logging.info(f"Deleted {result.rowcount} Lobby Data Transactions")



