# my_discord_bot/routes/example_routes.py
import logging
from typing import Optional

from discord.ext import commands
from fastapi import APIRouter, HTTPException, Request

from api.auth.auth import Auth
from classes.config.utils import ConfigUtils
from classes.configsetup import ConfigSetup
from classes.support.queue import Queue
from databases.transactions.ConfigData import ConfigData

router = APIRouter()


@router.get("/example")
async def example_route() :
	return {"message" : "Hello from the example route!"}

logger = logging.getLogger(__name__)



@router.post("/config/refresh/{guildid}")
async def refresh_config(request: Request, guildid: Optional[int]= None) :
	if not await Auth(request).verify() :
		# the error is usually raised in the verify function, but this is just a final catch.
		raise HTTPException(status_code=403)

	logging.info("Website Request: Reload Config")
	print("Website Request: Reload Config")
	if guildid is None :
		logging.info("[Config API] guildid not provided")
		return {"error" : "Guild ID is required"}
	ConfigData().load_guild(guildid)
	return {"message" : f"Config refresh queued for {guildid}"}


@router.post("/config/{guildid}/autosetup")
async def auto_setup(request: Request, guildid: int) :
	if not await Auth(request).verify() :
		# the error is usually raised in the verify function, but this is just a final catch.
		raise HTTPException(status_code=403)

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
	if not await Auth(request).verify() :
		# the error is usually raised in the verify function, but this is just a final catch.
		raise HTTPException(status_code=403)

	bot: commands.Bot = request.app.state.bot
	guild = bot.get_guild(guildid)
	if not guild :
		return {"message" : "Guild not found"}
	Queue().add(ConfigSetup().check_channel_permissions(guild))
	return {"message" : f"Permission check for {guild.name} queued"}

@router.post("/config/{guildid}/changes/log")
async def log_config_changes(request: Request, guildid: int, changes: dict, user_name: str = "dashboard_api") :
	if not await Auth(request).verify() :
		# the error is usually raised in the verify function, but this is just a final catch.
		raise HTTPException(status_code=403)

	bot: commands.Bot = request.app.state.bot
	guild = bot.get_guild(guildid)
	if not guild :
		return {"message" : "Guild not found"}
	await ConfigUtils.log_change(guild, changes, user_name)
	return {"message" : f"Configuration changes for {guild.name} logged"}