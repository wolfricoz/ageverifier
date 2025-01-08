# my_discord_bot/routes/example_routes.py
import json
import os

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import logging

from classes.databaseController import ConfigData

router = APIRouter()




@router.get("/example")
async def example_route() :
	return {"message" : "Hello from the example route!"}

@router.post("/config/refresh")
async def refresh_config(request: Request):
	print("Api Call received: Reload")
	token = request.headers.get('token')
	if token != os.getenv("API_KEY"):
		return
	ConfigData().reload()
	return {"message" : "Config refresh queued"}

