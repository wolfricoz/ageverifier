from dotenv import load_dotenv

from classes.encryption import Encryption
load_dotenv('.env')

#
# count = 0
# while count < 10:
# 	try:
# 		VerificationTransactions().add_idcheck(123456, 'test', True, 'test')
# 		count += 1
# 	except Exception as e:
# 		print(e)
# 		count += 1
#
# VerificationTransactions().add_idcheck(random.randint(100000, 1000000), 'test', True, 'test')

# Without r prefix, Python interprets \x as escape sequences
dob_encrypted = '\\x674141414141426f73304b3145773932374d64514570387132386f535578784b36776f654c4756366c496b65684870376c6b4c5a4c2d39644f37446176386b54796e3847543559523736544f74656d62636b6b5972483357695464387175505737413d3d'


result = Encryption().decrypt(dob_encrypted)
print(result)