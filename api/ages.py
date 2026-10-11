# my_discord_bot/routes/example_routes.py
import io
import logging
from typing import Annotated

import discord
from discord.ext import commands
from discord_py_utilities.messages import send_message
from fastapi import APIRouter, Body, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field, Json
from starlette.responses import JSONResponse

from api.auth.auth import Auth
from classes.alts import find_alts, format_alts
from classes.encryption import Encryption
from classes.support.queue import Queue
from classes.verification.process import VerificationProcess
from classes.verification.risk import calculate_risk
from databases.current import Users
from databases.transactions.ConfigData import ConfigData
from databases.transactions.UserTransactions import UserTransactions
from databases.transactions.VerificationTransactions import VerificationTransactions
from databases.transactions.WebsiteDataTransactions import WebsiteDataTransactions
from views.buttons.idreviewbuttons import IdReviewButton
from views.buttons.idwithdrawbutton import attach_withdraw_button

router = APIRouter()


class AgeVerification(BaseModel) :
	dob: str = Field(..., description="Date of birth in mm/dd/yyyy format")
	age: int = Field(..., description="Calculated or provided age of the user")
	guid: str = None
	ip: str = None
	vpn: bool = False
	vpn_score: int = 0
	fingerprint: str = None # SHA-256 of the member's browser traits, from the dashboard.
	free: bool = True # Check if its a subscribed server; we can pull it from the server too but this is just for debugging / future statistics.

class IdVerification(BaseModel) :
	guid: str = None
	ip: str = None
	vpn: bool = False
	vpn_score: int = 0
	fingerprint: str = None
	free: bool = True

class VerificationOpened(BaseModel) :
	guid: str = Field(..., description="The verification link's uuid")

@router.post("/age/opened/{guild_id}/{user_id}")
async def verification_opened(request: Request, guild_id: int, user_id: int, opened: VerificationOpened = Body()) :
	"""
	Called by the dashboard when the member loads the verification page. Only the first call
	for a link is recorded; it starts the abandoned link reminder timer.
	"""
	if not await Auth(request).verify() :
		# the error is usually raised in the verify function, but this is just a final catch.
		raise HTTPException(status_code=403)
	if not WebsiteDataTransactions().set_opened(opened.guid, user_id, guild_id) :
		return JSONResponse(
			status_code=404,
			content={"success" : False, "message" : "Verification link not found"},
		)
	return {"success" : True}


@router.post("/age/get/{user_id}")
async def fetch_age(request: Request, user_id: int) :
	if not await Auth(request).verify() :
		# the error is usually raised in the verify function, but this is just a final catch.
		raise HTTPException(status_code=403)
	userinfo: Users = UserTransactions().get_user(user_id)
	if userinfo is None :
		return {"message" : "No data found for this user"}

	# FUTURE: [SECURITY] This endpoint returns the fully decrypted date of birth of (potentially minor) users over the API. Even behind auth, exposing plaintext DOB is a significant privacy/GDPR concern — confirm this is required, restrict it, and audit-log access.
	# This is only used by the dashboard currently to review date of birth, because of that we'll be changing this in the future.
	return {
		"message"       : "Reminder: this information is only for verification purposes. Do not share this information with anyone.",
		"user_id"       : userinfo.uid,
		"date_of_birth" : Encryption().decrypt(userinfo.date_of_birth),
		"server"        : userinfo.server
	}


@router.post("/age/verify/{guild_id}/{user_id}")
async def verify_age(request: Request, guild_id: int, user_id: int, verification: AgeVerification = Body()) :
	if not await Auth(request).verify() :
		# the error is usually raised in the verify function, but this is just a final catch.
		raise HTTPException(status_code=403)
	guild = None
	# === Preparing the data ===


	if verification.dob.count("/") <2 :
		return {"success": False, "message" : "Invalid date format"}

	if verification.guid and WebsiteDataTransactions().owner_mismatch(verification.guid, user_id, guild_id) :
		return {"success" : False, "message" : "UserID does NOT match guid."}


	dob = verification.dob.split('/')  # this should always be mm/dd/yyyy
	age = verification.age
	bot: commands.Bot = request.app.state.bot
	try :
		try :
			guild = bot.get_guild(int(guild_id))
			if not guild :
				guild = await bot.fetch_guild(guild_id)
		except discord.NotFound :
			logging.error("guild not found", exc_info=True)
			return JSONResponse(
				status_code=404,
				content={"success" : False, "message" : "Guild not found"},
			)

		try :
			user = guild.get_member(int(user_id))
			if not user :
				user = await guild.fetch_member(user_id)
		except discord.NotFound :
			logging.warning(f"Member not found, may have left the server: {user_id} in {guild.name}", exc_info=True)
			return JSONResponse(
				status_code=404,
				content={"success" : False, "message" : "Member not found"},
			)

		alts = find_alts(user, verification.ip, verification.fingerprint)
		risk = calculate_risk(user.created_at, alts, verification.vpn, verification.vpn_score)
		vp = VerificationProcess(bot, user, guild, dob[1], dob[0], dob[2], age, alts=alts, risk=risk)
		msg = await vp.verify()

		if vp.error is not None :
			try :
				await send_message(user, f"Verification failed: {vp.error}")
			except (discord.Forbidden, discord.NotFound):
				logging.warning(f"Unable to send message to {user.name}")

			return {"success" : False, "message" : vp.discrepancy}
		try:
			if verification.guid :
				WebsiteDataTransactions().set_verified(verification.guid, user_id)
		except ValueError:
			return {"success" : False, "message" : "UserID does NOT match guid."}

		if vp.discrepancy is not None :
			id_check = True

			if vp.discrepancy in ["age_too_high", "mismatch", "below_minimum_age"] :
				id_check = False

			from classes.idcheck import IdCheck
			Queue().add(IdCheck.send_check_api(bot, user, guild,
			                                   vp.id_channel,
			                                   vp.discrepancy,
			                                   vp.age,
			                                   vp.dob,
			                                   date_of_birth=vp.recorded_dob,
			                                   years=vp.years if vp.years else None,
			                                   id_check=id_check,
			                                   id_check_reason=vp.id_check_info.reason if vp.id_check_info else vp.discrepancy,
			                                   server=vp.id_check_info.server if vp.id_check_info else guild.name
			                                   ), priority=1)

			if id_check :
				return {"success" : True, "message" : vp.discrepancy}

		return {"success" : True, "message" : msg}
	except Exception as e :
		try :
			guild = bot.get_guild(int(guild_id))
			if not guild :
				guild = await bot.fetch_guild(guild_id)
		except discord.NotFound :
			logging.error("guild not found", exc_info=True)
		if not guild :
			logging.error("guild not found", exc_info=True)
			raise HTTPException(500)
		channel = await ConfigData().get_channel(guild, "approval_channel")
		await send_message(channel, f"Website verification failed for {user_id} with error: {e}")

		raise HTTPException(500)

# Hard cap on ID uploads. Matches Discord's attachment limit, so anything accepted
# here can actually be forwarded to the user's DM and the mod channel. Note this is
# a separate concern from MultiPartParser.spool_max_size in main.py: that one only
# decides when the upload buffer rolls over to disk, it does not reject anything.
MAX_ID_FILE_SIZE = 25 * 1024 * 1024

@router.post("/age/idverify/{guild_id}/{user_id}")
async def verify_age(request: Request, guild_id: int, user_id: int, id_file: Annotated[UploadFile, File()], verification: Annotated[Json[IdVerification], Form()],) :
	"""
	This route verifies the user through ID verification.
	:param id_file:
	:param request:
	:param guild_id:
	:param user_id:
	:param verification:
	:return:
	"""

	# Verify the request
	if not id_file.filename.endswith(".jpg"):
		return JSONResponse(
			status_code=422,
			content={
				"success" : False,
				"message" : f"File extension must be .jpg",
			}
		)

	if id_file.size and id_file.size > MAX_ID_FILE_SIZE :
		return JSONResponse(
			status_code=422,
			content={
				"success" : False,
				"message" : f"File must be {MAX_ID_FILE_SIZE // (1024 * 1024)}MB or smaller.",
			}
		)

	if verification.guid and WebsiteDataTransactions().owner_mismatch(verification.guid, user_id, guild_id) :
		return {"success" : False, "message" : "UserID does NOT match guid."}

	# Fetch the data from the api
	try:
		bot: commands.Bot = request.app.state.bot
		guild = await fetch_guild(bot, guild_id)
		member = await fetch_member(guild, user_id)

	except Exception :
		return {"success" : False, "message" : 'Failed to load variables, please try again. Please ensure you are in the guild!'}
	try:
		mod_channel: discord.TextChannel = await ConfigData().get_channel(guild, "approval_channel")
	except Exception :
		return {
			"success" : False,
			"message" : "Moderation channel not set, please inform the staff!"
		}
	# create DM channel
	try:
		dm_channel = await member.create_dm()
		id_bytes = await id_file.read()

		message = await send_message(
			dm_channel,
			"Thank you — we received your ID for verification. Attached is a private copy of what you submitted.\n\n"
			"This message is the only storage location for your submission. We keep it on Discord for review only, for up to 7 days. "
			"When the review is complete, or 7 days pass (whichever comes first), this message will be deleted and no other copies will be kept.\n\n"
			"You can withdraw your consent at any time with the button below: it deletes your ID straight away and cancels the review.",
			files=[discord.File(fp=io.BytesIO(id_bytes), filename="id.jpg", spoiler=True)],
		)
	except Exception as e:
		logging.error(e)
		return {
			"success" : False,
			"message" : f"Failed to send DM to {member.name}!"
		}

	idcheck = VerificationTransactions().get_id_info(member.id)
	if idcheck and idcheck.idmessage :
		from classes.idcheck import IdCheck
		await IdCheck.remove_idmessage(member, idcheck)

	try :
		VerificationTransactions().add_idcheck(member.id, idcheck=False)
		VerificationTransactions().update_verification(member.id, idmessage=message.id)
	except Exception as e :
		logging.error(f"Failed to update ID record for {member.id} in {guild.name}: {e}", exc_info=True)
		await send_message(mod_channel, f"[ID record fail] Failed to update ID record, continuing verification.")
	embed = discord.Embed(
		title="ID Verification Submission",
		description=f"Submission from {member.mention}.",
		color=discord.Color.blue()
	)
	embed.add_field(
		name="Staff Notice",
		value="Do not share this ID outside of staff members responsible for verification or save this ID. Abuse will be grounds for immediate blacklisting.",
		inline=False
	)
	alts = find_alts(member, verification.ip, verification.fingerprint)
	if ConfigData().get_toggle(guild.id, "risk_score", default="ENABLED") :
		risk = calculate_risk(member.created_at, alts, verification.vpn, verification.vpn_score)
		embed.add_field(name="Risk Score", value=risk.format(), inline=False)
	if alt_names := format_alts(alts) :
		embed.add_field(name="Potential Alts", value=alt_names, inline=False)
	embed.set_footer(text=member.id)
	staff_message = await mod_channel.send(f"{member.mention} has submitted an ID for verification.", embed=embed,
	                                       view=IdReviewButton(reverify=False)) # This route can never be reverify.
	await attach_withdraw_button(message, staff_message)
	try :
		if verification.guid :
			WebsiteDataTransactions().set_verified(verification.guid, user_id)
	except ValueError :
		return {"success" : False, "message" : "UserID does NOT match guid."}

	return {"success" : True, "message" : "Thank you for verifying."}






# supporting functions (Maybe for the library?)
async def fetch_guild(bot, guild_id: int) :
		guild = bot.get_guild(guild_id)
		if not guild :
			guild = await bot.fetch_guild(guild_id)
		return guild

async def fetch_member(guild, user_id) :
	member = guild.get_member(user_id)
	if not member :
		member = await guild.fetch_member(user_id)
	return member