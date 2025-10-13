# my_discord_bot/routes/example_routes.py
import logging
import os
from datetime import datetime

import discord
from discord.ext import commands
from discord_py_utilities.messages import send_message
from fastapi import APIRouter, Request

from classes.encryption import Encryption
from classes.idcheck import IdCheck
from classes.verification.process import VerificationProcess
from databases.controllers.UserTransactions import UserTransactions
from databases.current import Users

router = APIRouter()



@router.post("/age/get/{user_id}")
async def refresh_config(request: Request, user_id: int):
	token = request.headers.get('token')
	if token != os.getenv("API_KEY"):
		return {"message": "Invalid token"}
	userinfo: Users = UserTransactions().get_user(user_id)
	if userinfo is None:
		return {"message": "No data found for this user"}

	return {
		"message": "Reminder: this information is only for verification purposes. Do not share this information with anyone.",
		"user_id": userinfo.uid,
		"date_of_birth": Encryption().decrypt(userinfo.date_of_birth),
		"server": userinfo.server
	}

@router.post("/age/verify/{guild_id}/{user_id}")
async def refresh_config(request: Request, guild_id, user_id: int):
	token = request.headers.get('token')
	if token != os.getenv("API_KEY"):
		return {"message": "Invalid token"}

	# === Preparing the data ===
	dob = request.query_params.get('dob').split('/') # this should always be mm/dd/yyyy
	age = request.query_params.get('age')
	bot: commands.Bot = request.app.state.bot

	try:
		user = bot.get_user(int(user_id))
		if not user:
			user = await bot.fetch_user(user_id)
		guild = bot.get_guild(int(guild_id))
		if not guild:
			guild = await bot.fetch_guild(guild_id)
	except discord.NotFound:
		logging.error("User or guild not found", exc_info=True)
		return {"message": "User or guild not found"}
	vp = VerificationProcess(bot, user, guild, dob[0], dob[1], dob[2], age)
	msg = await vp.verify()

	if vp.error is not None :
		try:
			await send_message(user, f"Verification failed: {vp.error}")
		except discord.Forbidden or discord.NotFound:
			logging.warning(f"Unable to send message to {user.name}")
		return
	if vp.discrepancy is not None :
		id_check = True
		if vp.discrepancy in ["age_too_high", "mismatch", "below_minimum_age"] :
			id_check = False

		return await IdCheck.send_check(interaction,
		                                vp.id_channel,
		                                vp.discrepancy,
		                                vp.age,
		                                vp.dob,
		                                id_check=id_check,
		                                id_check_reason=vp.id_check_info.reason,
		                                server=vp.id_check_info.server)

	return {"success": True, "message": msg}







