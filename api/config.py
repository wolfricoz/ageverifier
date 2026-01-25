# my_discord_bot/routes/example_routes.py
import logging
import os
from typing import Optional

from discord.ext import commands
from fastapi import APIRouter, Request

from classes.config.utils import ConfigUtils
from classes.configsetup import ConfigSetup
from classes.support.queue import Queue
from databases.transactions.ConfigData import ConfigData

router = APIRouter()


@router.get("/example")
async def example_route() :
	return {"message" : "Hello from the example route!"}


def verify_token(request: Request) :
	return request.headers.get('token') != os.getenv("API_KEY")


@router.post("/config/refresh")
async def refresh_config(request: Request, guildid: Optional[int]= None) :
	if verify_token(request) :
		logging.warning(f"Invalid token for config refresh request from ip {request.client.host}")

		return None
	logging.info("Website Request: Reload Config")
	if guildid is not None :
		ConfigData().load_guild(guildid)
		return {"message" : f"Config refresh queued for {guildid}"}
	ConfigData().reloading = True
	Queue().add(ConfigData().reload())
	return {"message" : "Config refresh queued"}


@router.post("/config/{guildid}/autosetup")
async def auto_setup(request: Request, guildid: int) :
	if verify_token(request) :
		logging.warning(f"Invalid token for auto setup request for {guildid} with ip {request.client.host}")
		return None

	bot: commands.Bot = request.app.state.bot
	guild = bot.get_guild(guildid)
	if not guild:
		guild = await bot.fetch_guild(guildid)
	if not guild :
		return {"message" : "Guild not found"}
	Queue().add(ConfigSetup().api_auto_setup(guild))
	ConfigData().load_guild(guildid)
	return {"message" : f"Auto Setup for {guild.name} queued"}


@router.post("/config/{guildid}/permissioncheck")
async def permission_check(request: Request, guildid: int) :
	if verify_token(request) :
		logging.warning(f"Invalid token for permission check request for {guildid} with ip {request.client.host}")

		return None

	bot: commands.Bot = request.app.state.bot
	guild = bot.get_guild(guildid)
	if not guild :
		return {"message" : "Guild not found"}
	Queue().add(ConfigSetup().check_channel_permissions(guild))
	return {"message" : f"Permission check for {guild.name} queued"}

@router.post("/config/{guildid}/changes/log")
async def log_config_changes(request: Request, guildid: int, changes: dict, user_name: str = "dashboard_api") :
	if verify_token(request) :
		logging.warning(f"Invalid token for config change log request for {guildid} with ip {request.client.host}")
		return None

	bot: commands.Bot = request.app.state.bot
	guild = bot.get_guild(guildid)
	if not guild :
		return {"message" : "Guild not found"}
	await ConfigUtils.log_change(guild, changes, user_name)
	return {"message" : f"Configuration changes for {guild.name} logged"}