import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import classes.charts as charts
import modules.Lobby as lobby_module
import modules.Stats as stats_module


def interaction() :
	return MagicMock(response=MagicMock(defer=AsyncMock()), followup=MagicMock(send=AsyncMock()))


class TestAgeChart(unittest.TestCase) :
	def chart(self, ages) :
		rows = [SimpleNamespace(date_of_birth=str(age)) for age in ages]
		with patch.object(charts, "Encryption") as encryption, \
				patch.object(charts.AgeCalculations, "dob_to_age", side_effect=lambda dob : int(dob)), \
				patch.object(charts.plt, "savefig") :
			encryption.return_value.decrypt.side_effect = lambda value : value
			return charts.AgeCharts(rows).getAgeDistributionChart()

	def test_nothing_to_chart_returns_none(self) :
		self.assertIsNone(self.chart([]))

	def test_boundary_ages_are_counted(self) :
		chart = self.chart([18, 24, 25, 34])

		self.assertIsNotNone(chart)


class TestStatsCommands(unittest.TestCase) :
	def test_average_ages_says_so_when_there_is_no_data(self) :
		inter = interaction()
		with patch.object(stats_module, "JoinHistoryTransactions"), \
				patch.object(stats_module.AgeCharts, "getAgeDistributionChart", return_value=None) :
			asyncio.run(stats_module.Stats.average_ages_graph.callback(MagicMock(), inter))

		inter.response.defer.assert_awaited_once()
		self.assertIn("nothing to chart", inter.followup.send.await_args.args[0])

	def test_graph_answers_the_interaction(self) :
		inter = interaction()
		chart = MagicMock(filename="chart.png")
		with patch.object(stats_module, "JoinHistoryTransactions"), \
				patch.object(stats_module, "JoinHistoryCharts", return_value=chart), \
				patch.object(stats_module.discord, "File") :
			asyncio.run(stats_module.Stats.server.callback(MagicMock(), inter, 7))

		inter.response.defer.assert_awaited_once()
		inter.followup.send.assert_awaited_once()
		chart.clean_up_chart.assert_called_once()


class TestAgecheck(unittest.TestCase) :
	def test_stops_after_an_invalid_date(self) :
		send = AsyncMock()
		with patch.object(lobby_module.AgeCalculations, "validatedob", AsyncMock(return_value=False)), \
				patch.object(lobby_module.AgeCalculations, "dob_to_age") as dob_to_age, \
				patch.object(lobby_module, "send_response", send) :
			asyncio.run(lobby_module.Lobby.agecheck.callback(MagicMock(), MagicMock(), "18/06/1997"))

		dob_to_age.assert_not_called()
		send.assert_not_awaited()

	def test_uses_the_validated_date(self) :
		send = AsyncMock()
		with patch.object(lobby_module.AgeCalculations, "validatedob", AsyncMock(return_value="06/18/1997")), \
				patch.object(lobby_module.AgeCalculations, "dob_to_age", return_value=29) as dob_to_age, \
				patch.object(lobby_module, "send_response", send) :
			asyncio.run(lobby_module.Lobby.agecheck.callback(MagicMock(), MagicMock(), "6/18/1997"))

		dob_to_age.assert_called_once_with("06/18/1997")
		self.assertIn("29 years old", send.await_args.args[1])


if __name__ == '__main__' :
	unittest.main()
