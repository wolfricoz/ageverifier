# my_discord_bot/routes/example_routes.py
import json
import os

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import logging

from classes.databaseController import ConfigData, UserTransactions
from classes.encryption import Encryption
from databases.current import Users

router = APIRouter()





@router.post("/age/get/{user_id}")
async def refresh_config(request: Request, user_id: int):
	token = request.headers.get('token')
	if token != os.getenv("API_KEY"):
		return {"message": "Invalid token"}
	userinfo: Users = UserTransactions.get_user(user_id)
	if userinfo is None:
		return {"message": "No data found for this user"}

	return {
		"message": "Reminder: this information is only for verification purposes. Do not share this information with anyone.",
		"user_id": userinfo.uid,
		"date_of_birth": Encryption().decrypt(userinfo.date_of_birth),
		"server": userinfo.server
	}

