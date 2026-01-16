import discord
import matplotlib
from discord import app_commands
from discord.ext import commands

from classes.charts import AgeCharts, JoinHistoryCharts
from classes.retired.discord_tools import send_message

matplotlib.use('Agg')

from databases.transactions.HistoryTransactions import JoinHistoryTransactions


class Stats(commands.GroupCog, name="stats") :
	"""
	Welcome to the Statistics Zone!
	This set of commands allows you to visualize various server statistics, such as member activity and age demographics.
	It's a great way to get a snapshot of your community's health and composition.
	These commands are available to everyone.
	"""
	def __init__(self, bot: commands.Bot) :
		self.bot = bot

	@app_commands.command(name="graph", description="Get a graph of joins and leaves")
	async def server(self, interaction: discord.Interaction, days: int = 7) :
		"""
		Curious about your server's growth? This command generates a graph showing the number of members who have joined and left your server over a specific period.
		You can specify the number of days you want to look back on. It's a fantastic tool for tracking membership trends!
		"""
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
		"""
		Want to see the bigger picture? This command shows the total number of joins and leaves across all servers using this bot.
		It provides a global perspective on user activity.
		"""
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
		"""
		Get a visual breakdown of the age demographics in your server! This command creates a pie chart showing the distribution of different age groups among your verified members.
		It's a great way to understand the age range of your community.
		"""
		data = JoinHistoryTransactions().age_graph_data(interaction.guild.id)
		chart = AgeCharts(data)
		chart.getAgeDistributionChart()
		await send_message(interaction.channel, 'Pie chart of age distributions', files=[discord.File(chart.filename, filename=chart.filename)])
		chart.clean_up_chart()



async def setup(bot) :
	"""Adds the cog to the bot."""
	await bot.add_cog(Stats(bot))
