from classes.charts import AgeCharts, JoinHistoryCharts
from databases.controllers.HistoryTransactions import JoinHistoryTransactions

# age graph test

data = JoinHistoryTransactions().age_graph_data(1022307023527890974)
print(data)
graph = AgeCharts(data)
graph.getAgeDistributionChart()

# Join History Graph Testing
DAYS = 30
data2 = JoinHistoryTransactions().join_leave_graph_data(1022307023527890974, DAYS)
graph2 = JoinHistoryCharts(data2, DAYS).getBarChart()


test = JoinHistoryTransactions().fetch_previous_verifications(474365489670389771)
print(test)