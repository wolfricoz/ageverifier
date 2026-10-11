import os
import unittest
from unittest.mock import patch

from classes.banwatch import BanWatch


class TestBanWatchSettings(unittest.IsolatedAsyncioTestCase) :

	def test_settings_are_read_on_use(self) :
		# Set after classes.banwatch was imported, as happens when .env is loaded late.
		with patch.dict(os.environ, {"BANWATCH_URL" : "https://banwatch.test", "BANWATCH_TOKEN" : "token"}) :
			banwatch = BanWatch()
			self.assertEqual(banwatch.urlbuilder("bans/count/1"), "https://banwatch.test/bans/count/1")
			self.assertEqual(banwatch.auth_token, "token")

	async def test_no_request_without_a_url(self) :
		with patch.dict(os.environ, {}, clear=False) :
			os.environ.pop("BANWATCH_URL", None)
			with patch("classes.banwatch.aiohttp.ClientSession") as session :
				self.assertIsNone(await BanWatch().fetchBanCount(1))
				session.assert_not_called()


if __name__ == '__main__' :
	unittest.main()
