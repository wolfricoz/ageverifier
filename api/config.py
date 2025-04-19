# my_discord_bot/routes/example_routes.py
import json
import os

import discord.ext.commands
from discord.utils import get
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import logging
from discord.ext import commands

from classes.configsetup import ConfigSetup
from classes.databaseController import ConfigData
from classes.support.queue import queue
from resources.data.config_variables import rolechoices, channelchoices, messagechoices

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

		return
	logging.info("Website Request: Reload Config")

	ConfigData().reload()
	return {"message" : "Config refresh queued"}


@router.post("/config/{guildid}/autosetup")
async def auto_setup(request: Request, guildid: int) :
	if verify_token(request) :
		logging.warning(f"Invalid token for auto setup request for {guildid} with ip {request.client.host}")
		return

	bot: commands.Bot = request.app.state.bot
	guild = bot.get_guild(guildid)
	if not guild :
		return {"message" : "Guild not found"}
	queue().add(ConfigSetup().api_auto_setup(guild))
	ConfigData().reload()
	return {"message" : f"Auto Setup for {guild.name} queued"}


@router.post("/config/{guildid}/permissioncheck")
async def permission_check(request: Request, guildid: int) :
	if verify_token(request) :
		logging.warning(f"Invalid token for permission check request for {guildid} with ip {request.client.host}")

		return

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
	queue().add(ConfigSetup().check_channel_permissions(mod_channel))
	return {"message" : f"Permission check for {guild.name} queued"}
