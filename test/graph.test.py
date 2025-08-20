from classes.charts import AgeCharts
from classes.encryption import Encryption
from databases.controllers.HistoryTransactions import JoinHistoryTransactions
from classes.AgeCalculations import AgeCalculations

data = JoinHistoryTransactions().age_graph_data(1022307023527890974)
graph_data = {}

for row in data:
	if row.user.date_of_birth is None:
		continue
	dob = Encryption().decrypt(row.user.date_of_birth)
	age = AgeCalculations.dob_to_age(dob)
	if str(age) not in graph_data.keys():
		graph_data[str(age)] = 0
	graph_data[str(age)] += 1

print(graph_data)
chart = AgeCharts(None, data)
chart.getAgeDistributionChart()
# print(data)
