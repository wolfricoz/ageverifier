# my_discord_bot/routes/example_routes.py

from fastapi import APIRouter

from classes.databaseController import DatabaseTransactions
from classes.support.queue import queue

router = APIRouter()


@router.post("/ping")
async def ping() :
	DatabaseTransactions.ping_db()
	q = queue()
	return {
		"status"                : "alive",
		"high_priority_queue"   : len(q.high_priority_queue),
		"normal_priority_queue" : len(q.normal_priority_queue),
		"low_priority_queue"    : len(q.low_priority_queue),
	}
