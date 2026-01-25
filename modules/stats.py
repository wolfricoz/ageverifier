import discord
import matplotlib
from discord import app_commands
from discord.ext import commands

from classes.charts import AgeCharts, JoinHistoryCharts
from classes.retired.discord_tools import send_message

matplotlib.use('Agg')

from databases.transactions.HistoryTransactions import JoinHistoryTransactions


class Stats(commands.GroupCog, name="stats") :
	def __init__(self, bot: commands.Bot) :
		self.bot = bot

	@app_commands.command(name="graph", description="Get a graph of joins and leaves")
	async def server(self, interaction: discord.Interaction, days: int = 7) :
		data = JoinHistoryTransactions().join_leave_graph_data(interaction.guild.id, days)
		chart = JoinHistoryCharts(data, days)
		if days < 30 :
			chart.getBarChart()
		else :
			chart.getPieChart()
		# Send the file via discord
		await send_message(interaction.channel, 'Bar Graph of Joins and Leaves',
		                   files=[discord.File(chart.filename, filename=chart.filename)])
		chart.clean_up_chart()




	@app_commands.command(name="graph_all", description="Get a graph of joins and leaves")
	async def all_bar_graph(self, interaction: discord.Interaction, days: int = 7) :
		data = JoinHistoryTransactions().join_leave_graph_data(None, days)
		chart = JoinHistoryCharts(data, days)
		if days < 30:
			chart.getBarChart()
		else:
			chart.getPieChart()
		# Send the file via discord
		await send_message(interaction.channel, 'Bar Graph of Joins and Leaves (global)', files=[discord.File(chart.filename, filename=chart.filename)])
		chart.clean_up_chart()

	@app_commands.command(name="average_ages", description="Get a graph of the average ages in the server")
	async def average_ages_graph(self, interaction: discord.Interaction) :
		data = JoinHistoryTransactions().age_graph_data(interaction.guild.id)
		chart = AgeCharts(data)
		chart.getAgeDistributionChart()
		await send_message(interaction.channel, 'Pie chart of age distributions', files=[discord.File(chart.filename, filename=chart.filename)])
		chart.clean_up_chart()



async def setup(bot) :
	"""Adds the cog to the bot."""
	await bot.add_cog(Stats(bot))
