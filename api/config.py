# my_discord_bot/routes/example_routes.py
import logging
import os

from discord.ext import commands
from fastapi import APIRouter, Request

from classes.configsetup import ConfigSetup
from classes.support.queue import Queue
from databases.controllers.ConfigData import ConfigData

router = APIRouter()


@router.get("/example")
async def example_route() :
	return {"message" : "Hello from the example route!"}


def verify_token(request: Request) :
	return request.headers.get('token') != os.getenv("API_KEY")


@router.post("/config/refresh")
async def refresh_config(request: Request) :
	if verify_token(request) :
		logging.warning(f"Invalid token for config refresh request from ip {request.client.host}")

		return None
	logging.info("Website Request: Reload Config")

	ConfigData().reload()
	return {"message" : "Config refresh queued"}


@router.post("/config/{guildid}/autosetup")
async def auto_setup(request: Request, guildid: int) :
	if verify_token(request) :
		logging.warning(f"Invalid token for auto setup request for {guildid} with ip {request.client.host}")
		return None

	bot: commands.Bot = request.app.state.bot
	guild = bot.get_guild(guildid)
	if not guild :
		return {"message" : "Guild not found"}
	Queue().add(ConfigSetup().api_auto_setup(guild))
	ConfigData().reload()
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
	try :
		mod_channel = bot.get_channel(ConfigData().get_key_int(guildid, "lobbymod"))
		if mod_channel is None :
			return {"message" : "No moderation channel set"}
	except :
		return {"message" : "No moderation channel set"}
	Queue().add(ConfigSetup().check_channel_permissions(mod_channel))
	return {"message" : f"Permission check for {guild.name} queued"}
