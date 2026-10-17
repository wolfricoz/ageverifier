import os
import sys
import unittest

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), 'main.env'))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
loader = unittest.TestLoader()
start_dir = os.path.join(os.path.dirname(__file__), 'test_modules')
# Optional file pattern to run part of the suite, e.g. `python tests/run_tests.py test_config*.py`.
pattern = sys.argv[1] if len(sys.argv) > 1 else 'test*.py'
suite = loader.discover(start_dir, pattern=pattern)

from sqlalchemy_utils import drop_database
from databases.current import engine

assert engine.url.database.endswith('_test'), f"Refusing to run tests against {engine.url.database}"
# These load the root .env on import. Importing them here, before the pop below, keeps a test that first imports
# one of them from putting DISCORD_TOKEN back, which made the production guard block clear_bot_database (STR-91).
import classes.encryption, classes.iphash, modules.logs  # noqa: E401,F401
os.environ.pop('DISCORD_TOKEN', None)
try :
	# durations lists the slowest tests, so a slow test shows up in every run.
	runner = unittest.TextTestRunner(durations=10)
	result = runner.run(suite)
finally :
	# Tests use a connection pool; Postgres refuses to drop a database that still has open connections.
	engine.dispose()
	drop_database(engine.url)
# Exit with a non-zero status code if tests failed
sys.exit(not result.wasSuccessful())
