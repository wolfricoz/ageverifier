from datetime import datetime, timedelta

import discord
import matplotlib
from discord import app_commands
from discord.ext import commands
from discord_py_utilities.messages import send_message

from classes.access import AccessControl
from classes.charts import AgeCharts, JoinHistoryCharts
from classes.support.weeklyreport import rate

matplotlib.use('Agg')

from databases.transactions.HistoryTransactions import JoinHistoryTransactions
from databases.transactions.StatsTransactions import StatsTransactions

# website_data rows are deleted after 90 days (WebsiteDataTransactions.clean_table), so looking further back shows nothing.
MAX_FUNNEL_DAYS = 90


def website_funnel_embed(funnel: dict, days: int) -> discord.Embed :
	"""The server's online verification links from the last `days` days, and how far members got."""
	not_opened = funnel["created"] - funnel["opened"]
	embed = discord.Embed(title="🌐 Website verification funnel",
	                      description=f"Verification links created in the last {days} day(s)",
	                      color=discord.Color.teal())
	embed.add_field(name="Funnel", inline=False, value="\n".join([
		f"Links created: **{funnel['created']:,}**",
		f"Opened the page: **{funnel['opened']:,}** ({rate(funnel['opened'], funnel['created'])})",
		f"Never opened: **{not_opened:,}** ({rate(not_opened, funnel['created'])})",
		f"Verified: **{funnel['verified']:,}** ({rate(funnel['verified'], funnel['created'])})",
		f"Opened but not finished: **{funnel['abandoned']:,}** ({rate(funnel['abandoned'], funnel['opened'])} of opened)",
	]))
	embed.add_field(name="Reminders", inline=False, value="\n".join([
		f"Reminded: **{funnel['reminded']:,}**",
		f"Finished after the reminder: **{funnel['after_reminder']:,}** "
		f"({rate(funnel['after_reminder'], funnel['reminded'])})",
	]) if funnel["reminded"] else "None sent. `/config verification_reminder` DMs members who leave the page unfinished.")
	embed.set_footer(text="Opened but not finished includes members who are still on the page. "
	                      "The dashboard's Verification Insights page shows which step they stop at.")
	return embed


class Stats(commands.GroupCog, name="stats", description="Commands for visualizing server statistics.") :
	"""
	Welcome to the Statistics Zone!
	This set of commands allows you to visualize various server statistics, such as member activity and age demographics.
	It's a great way to get a snapshot of your community's health and composition.
	These commands are available to everyone, except `/stats verification`, which needs premium and `Manage Server`.
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

	@app_commands.command(name="verification", description="See where members drop out of website verification")
	@app_commands.checks.has_permissions(manage_guild=True)
	@AccessControl().check_premium()
	async def verification_funnel(self, interaction: discord.Interaction,
	                              days: app_commands.Range[int, 1, MAX_FUNNEL_DAYS] = 30) :
		"""
		See how far members get with website verification: how many links were created, how many members opened the
		page, how many finished, and how many left it unfinished. Covers links created in the last `days` days
		(default 30, up to 90). This is a premium feature.

		**Permissions:**
		- Requires `Manage Server` permission.
		"""
		await interaction.response.defer(ephemeral=True)
		end = datetime.now()
		funnel = StatsTransactions().website_funnel(end - timedelta(days=days), end, interaction.guild.id)
		await interaction.followup.send(embed=website_funnel_embed(funnel, days), ephemeral=True)


async def setup(bot) :
	"""Adds the cog to the bot."""
	await bot.add_cog(Stats(bot))
