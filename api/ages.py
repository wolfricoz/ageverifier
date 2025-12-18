# my_discord_bot/routes/example_routes.py
import logging
import os
from datetime import datetime

import discord
from discord.ext import commands
from discord_py_utilities.messages import send_message
from fastapi import APIRouter, Body, Request
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse

from classes.encryption import Encryption
from classes.support.queue import Queue
from classes.verification.process import VerificationProcess
from databases.controllers.UserTransactions import UserTransactions
from databases.controllers.WebsiteDataTransactions import WebsiteDataTransactions
from databases.current import Users

router = APIRouter()



class AgeVerification(BaseModel):
    dob: str = Field(..., description="Date of birth in mm/dd/yyyy format")
    age: int = Field(..., description="Calculated or provided age of the user")
    guid: str = None

@router.post("/age/get/{user_id}")
async def fetch_age(request: Request, user_id: int):
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
async def verify_age(request: Request, guild_id: int, user_id: int, verification: AgeVerification = Body() ):
	token = request.headers.get('token')
	if token != os.getenv("API_KEY"):
		return {"message": "Invalid token"}

	# === Preparing the data ===
	dob = verification.dob.split('/') # this should always be mm/dd/yyyy
	age = verification.age
	bot: commands.Bot = request.app.state.bot

	try:
		guild = bot.get_guild(int(guild_id))
		if not guild:
			guild = await bot.fetch_guild(guild_id)
	except discord.NotFound:
		logging.error("guild not found", exc_info=True)
		return JSONResponse(
			status_code=404,
			content={"success": False, "message": "Guild not found"},
		)

	try:
		user = guild.get_member(int(user_id))
		if not user:
			user = await guild.fetch_member(user_id)
	except discord.NotFound:
		logging.warning("Member not found, may have left the server", exc_info=True)
		return JSONResponse(
			status_code=404,
			content={"success" : False, "message" : "Member not found"},
		)


	vp = VerificationProcess(bot, user, guild, dob[1], dob[0],  dob[2], age)
	msg = await vp.verify()

	if vp.error is not None :
		try:
			await send_message(user, f"Verification failed: {vp.error}")
		except discord.Forbidden or discord.NotFound:
			logging.warning(f"Unable to send message to {user.name}")

		return {"success": False, "message": vp.discrepancy}
	if verification.guid:
		WebsiteDataTransactions().set_verified(verification.guid)

	if vp.discrepancy is not None :
		id_check = True


		if vp.discrepancy in ["age_too_high", "mismatch", "below_minimum_age"] :
			id_check = False
		from classes.idcheck import IdCheck
		Queue().add(IdCheck.send_check_api(user, guild,
		                                vp.id_channel,
		                                vp.discrepancy,
		                                vp.age,
		                                vp.dob,
		                                id_check=id_check,
		                                id_check_reason=vp.id_check_info.reason,
		                                server=vp.id_check_info.server))
		if id_check:
			return {"success": True, "message": vp.discrepancy}

	return {"success": True, "message": msg}







