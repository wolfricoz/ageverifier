import os
import sys
import unittest

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), 'main.env'))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
loader = unittest.TestLoader()
start_dir = os.path.join(os.path.dirname(__file__), 'test_modules')
suite = loader.discover(start_dir)

from sqlalchemy_utils import drop_database
from databases.current import engine

assert engine.url.database.endswith('_test'), f"Refusing to run tests against {engine.url.database}"
# Some modules load the root .env during discovery; without this the production guard blocks drop_bot_database (STR-91).
os.environ.pop('DISCORD_TOKEN', None)
try :
	runner = unittest.TextTestRunner()
	result = runner.run(suite)
finally :
	drop_database(engine.url)
# Exit with a non-zero status code if tests failed
sys.exit(not result.wasSuccessful())