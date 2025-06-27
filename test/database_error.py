import random

from classes.databaseController import VerificationTransactions
count = 0
while count < 10:
	try:
		VerificationTransactions.add_idcheck(123456, 'test', True, 'test')
		count += 1
	except Exception as e:
		print(e)
		count += 1

VerificationTransactions.add_idcheck(random.randint(100000, 1000000), 'test', True, 'test')
