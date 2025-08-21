import os

import numpy as np
from matplotlib import pyplot as plt

from classes.AgeCalculations import AgeCalculations
from classes.encryption import Encryption

plt.rcParams['axes.axisbelow'] = True
plt.rcParams['axes.spines.left'] = False
plt.rcParams['axes.spines.right'] = False
plt.rcParams['axes.spines.top'] = False
plt.rcParams['axes.spines.bottom'] = False
plt.rcParams['xtick.bottom'] = False
plt.rcParams['ytick.left'] = False


class JoinHistoryCharts():

	def __init__(self, data, days):
		self.data = data
		self.days = days
		self.filename = ""

	def getBarChart(self):
		# Organize data by status and then by date
		# This function was made by Gemini as a proof of concept, improved by humans.
		graph_data = {
			'NEW'      : {},
			'FAILED'   : {},
			'SUCCESS'  : {},
			'IDCHECK'  : {},
			'VERIFIED' : {}
		}

		for d in self.data :
			status = d.get('status')
			date = d.get('date_created')
			records = d.get('records', 0)
			if status and date :
				# Use the date as the key to accumulate records
				if date not in graph_data[status] :
					graph_data[status][date] = 0
				graph_data[status][date] += records

		# Get a unique list of all dates
		all_dates = sorted(list(set(d.get('date_created') for d in self.data if d.get('date_created'))))

		# Ensure all statuses have a record for all dates to prevent misalignment
		for status in graph_data :
			for date in all_dates :
				if date not in graph_data[status] :
					graph_data[status][date] = 0

		# Re-organize data into lists for plotting, preserving date order
		plot_data = {
			'NEW'      : [graph_data['NEW'][date] for date in all_dates],
			'FAILED'   : [graph_data['FAILED'][date] for date in all_dates],
			'SUCCESS'  : [graph_data['SUCCESS'][date] for date in all_dates],
			'IDCHECK'  : [graph_data['IDCHECK'][date] for date in all_dates],
			'VERIFIED' : [graph_data['VERIFIED'][date] for date in all_dates]
		}

		# plt.style.use()

		fig, ax = plt.subplots(figsize=(12, 5))

		# Set bar width
		bar_width = 0.5
		index = np.arange(len(all_dates))

		# Create a list of status labels and their corresponding data
		statuses = list(plot_data.keys())

		# Initialize a "bottom" array to keep track of the cumulative height of the bars
		bottom = np.zeros(len(all_dates))

		# Plot a bar for each status, with an offset for each one
		for status in statuses :
			ax.bar(index, plot_data[status], bar_width, label=status, bottom=bottom)
			# Update the bottom for the next set of bars
			bottom += plot_data[status]

		# Set the title and labels
		ax.set_title(f'Daily Records by Status (Last {self.days} Days)')
		ax.set_ylabel('Records')

		# Set the x-ticks and labels to show the dates
		ax.set_xticks(index)
		ax.set_xticklabels(all_dates, rotation=45, ha='right')

		# Add a legend
		ax.legend(title='Status', ncols=5, loc='upper center', framealpha=1.0)
		plt.grid(True, color='gray', linestyle='--', alpha=0.6, axis='y')

		plt.tight_layout()


		# Save the plot
		self.filename = 'records_by_status_stacked_bar_graph.png'
		plt.savefig(self.filename)
		return self

	def getPieChart(self) :
		graph_data = {
			'NEW'      : 0,
			'FAILED'   : 0,
			'SUCCESS'  : 0,
			'IDCHECK'  : 0,
			'VERIFIED' : 0,
		}

		for d in self.data :
			status = d.get('status')
			date = d.get('date_created')
			records = d.get('records', 0)
			if status and date :
				# Use the date as the key to accumulate records
				graph_data[status] += records
		fig, ax = plt.subplots(figsize=(12, 5))
		explode = (0,0,0.1,0,0)
		ax.pie(graph_data.values(), labels=list(graph_data.keys()), autopct='%1.1f%%', explode=explode)

		ax.set_title(f'Join history stats (Last {self.days} Days)')

		# Add a legend
		# ax.legend(title='Status', ncols=5, loc='upper center', framealpha=1.0)
		# plt.grid(True, color='gray', linestyle='--', alpha=0.6, axis='y')

		plt.tight_layout()
		self.filename = 'records_by_status_pie_chart.png'
		plt.savefig(self.filename)
		return self


	def clean_up_chart(self):
		os.remove(self.filename)
		return self


class AgeCharts():
	def __init__(self, data):
		self.filename = None
		self.data = data

	def getAgeDistributionChart(self) :
		graph_data = {}
		age_groups = {
			"18-24" : {
				"name"  : "18-24",
				"start" : 18,
				"end"   : 24
			},
			"25-34" : {
				"name"  : "25-34",
				"start" : 25,
				"end"   : 34
			},
			"35-44" : {
				"name"  : "35-44",
				"start" : 35,
				"end"   : 44
			},
			"45-54" : {
				"name"  : "45-54",
				"start" : 45,
				"end"   : 54
			},
			"55-64" : {
				"name"  : "55-64",
				"start" : 55,
				"end"   : 64
			},
			"65+"   : {
				"name"  : "65+",
				"start" : 65,
				"end"   : 200
			}
		}

		for row in self.data :
			if row.user.date_of_birth is None :
				continue
			dob = Encryption().decrypt(row.user.date_of_birth)
			age = AgeCalculations.dob_to_age(dob)
			for age_group in age_groups.values() :
				age_group: dict
				if age_group.get('start', 18) < age < age_group.get('end', 200) :
					if age_group.get('name') not in graph_data :
						graph_data[age_group.get('name')] = 0
					graph_data[age_group.get('name')] += 1
					break
		print(graph_data)
		self.filename = 'age_distribution_chart.png'
		fig, ax = plt.subplots(figsize=(12, 5))
		ax.pie(graph_data.values(), labels=list(graph_data.keys()), autopct='%1.1f%%')

		ax.set_title(f'Age distribution of joined members')

		# Add a legend
		# ax.legend(title='Status', ncols=5, loc='upper center', framealpha=1.0)
		# plt.grid(True, color='gray', linestyle='--', alpha=0.6, axis='y')

		plt.tight_layout()
		self.filename = 'age_distribution_pie_chart.png'
		plt.savefig(self.filename)
		return self


	def clean_up_chart(self):
		os.remove(self.filename)
		return self
