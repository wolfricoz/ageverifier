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
	print("Api Call received: Reload")
	if verify_token(request) :
		return
	ConfigData().reload()
	return {"message" : "Config refresh queued"}


@router.post("/config/{guildid}/autosetup")
async def refresh_config(request: Request, guildid: int) :
	if verify_token(request) :
		return

	bot: commands.Bot = request.app.state.bot
	guild = bot.get_guild(guildid)
	if not guild :
		return {"message" : "Guild not found"}
	queue().add(ConfigSetup().api_auto_setup(guild))
	ConfigData().reload()
	return {"message" : f"Auto Setup for {guild.name} queued"}

@router.post("/config/{guildid}/permissioncheck")
async def refresh_config(request: Request, guildid: int) :
	if verify_token(request) :
		return

	bot: commands.Bot = request.app.state.bot
	guild = bot.get_guild(guildid)
	if not guild :
		return {"message" : "Guild not found"}
	try:
		mod_channel = bot.get_channel(ConfigData().get_key_int(guildid, "lobbymod"))
		if mod_channel is None:
			return {"message": "No moderation channel set"}
	except:
		return {"message": "No moderation channel set"}
	queue().add(ConfigSetup().check_channel_permissions(mod_channel))
	return {"message" : f"Permission check for {guild.name} queued"}
