import discord
from discord.ext import commands

import databases.current
from classes.AgeCalculations import AgeCalculations
from classes.lobbyprocess import LobbyProcess
from classes.lobbytimers import LobbyTimers
from databases.controllers.AgeRoleTransactions import AgeRoleTransactions
from databases.controllers.ConfigData import ConfigData
from databases.controllers.HistoryTransactions import JoinHistoryTransactions
from databases.controllers.UserTransactions import UserTransactions
from databases.enums.joinhistorystatus import JoinHistoryStatus
from views.buttons.approvalbuttons import ApprovalButtons


class VerificationProcess :
	def __init__(self,
	             bot: commands.Bot,
	             user: discord.User,
	             guild: discord.Guild,
	             day: str,
	             month: str,
	             year: str,
	             age: int | str,
	             ) :
		self.bot = bot
		self.user = user
		self.user_record = None
		self.guild = guild
		self.day = day
		self.month = month
		self.year = year
		self.age = age
		self.mod_channel = None
		self.id_channel = None
		self.discrepancy = None
		self.id_check_info = None
		self.error = None
		self.dob = None

	async def verify(self) :
		try :
			# === Data validation starts here ===
			await self.load_data()

			dob = await AgeCalculations.validate_user_info(self.user, self.age, f"{self.month}/{self.day}/{self.year}",
			                                               self.mod_channel)
			self.dob = dob
			agechecked, years = AgeCalculations.agechecker(self.age, dob)
			self.age = int(self.age)
			# Check if user is underaged or below minimum age
			if self.check_underage(years):
				return self.discrepancy

			# Checks if the user is below the minimum age for the server.
			if self.check_minimum_age():
				return self.discrepancy

			# Check if users made any mistakes; prevent unnecessary ID checks.
			if self.check_typos(agechecked):
				return self.discrepancy

			# Checks if user has a date of birth in the database, and if the date of births match.
			if self.check_record(dob):
				return self.discrepancy

			# Checks if user is on the id list
			if self.check_id_record():
				return self.discrepancy

			# To be added: Check username for suspicious patterns.

			# === Validation finished, we now start processing the user ===
			automatic_status = ConfigData().get_key_or_none(self.guild.id, "automatic")
			if automatic_status and automatic_status == "enabled".upper() :
				await LobbyProcess.approve_user(self.guild, self.user, dob, self.age, "Automatic")
				return "Thank you for submitting your age and date of birth! You’ve been automatically verified and granted access."

			await AgeCalculations.check_history(self.guild.id, self.user, self.mod_channel)
			LobbyTimers().add_cooldown(self.guild.id, self.user.id, ConfigData().get_key_int_or_zero(self.guild.id, 'COOLDOWN'))
			approval_buttons = ApprovalButtons(age=self.age, dob=dob, user=self.user)
			await approval_buttons.send_message(self.guild, self.user, self.mod_channel)

			return "Your age and date of birth have been submitted successfully. A staff member will review your verification shortly to ensure everything checks out."

		except discord.Forbidden :
			self.error = "Ageverifier is missing permissions, please use `/config permissioncheck` to test permissions."
		except discord.NotFound :
			self.error = "Ageverifier could not fetch one of the channels, please use `/config view` and check if the channels still exist, and if ageverifier has permissions to view them."
		except Exception as e :
			self.error = e


	async def load_data(self) :
		"""Loads the data for the verification process and verifies it."""
		if self.age is None or self.day is None or self.month is None or self.year is None or self.user is None or self.guild is None :
			raise Exception("Missing data for verification: " +
			                f"age: {self.age}, day: {self.day}, month: {self.month}, year: {self.year}, user: {self.user}, guild: {self.guild}")
		self.user_record: databases.current.Users = UserTransactions().get_user(self.user.id)
		mod_lobby = ConfigData().get_key_int_or_zero(self.guild.id, "lobbymod")
		id_log = ConfigData().get_key_int_or_zero(self.guild.id, "idlog")
		if mod_lobby is None or id_log is None :
			raise Exception("Lobbymod or id_channel not set, inform the server staff to setup the server.")
		self.mod_channel = self.guild.get_channel(mod_lobby)
		self.id_channel = self.guild.get_channel(id_log)
		if self.id_channel is None :
			self.id_channel = self.guild.fetch_channel(id_log)
		if self.mod_channel is None :
			self.mod_channel = self.guild.fetch_channel(mod_lobby)

	def check_underage(self, years) :
		"""Checks if the user is underage."""
		if int(self.age) < 18 or int(years) < 18 :
			JoinHistoryTransactions().update(self.user.id, self.guild.id, JoinHistoryStatus.IDCHECK)
			self.discrepancy = "underage"
			return True
		return None

	def check_minimum_age(self) :
		"""Checks if the user is below the minimum age."""
		minimum_age = AgeRoleTransactions().get_minimum_age(self.guild.id)
		if minimum_age and self.age < minimum_age :
			self.discrepancy = "below_minimum_age"
			return True
		return None

	def check_typos(self, agechecked) :
		"""Checks if the user has any typos in their age."""
		if self.age > 200 :
			self.discrepancy = "age_too_high"
			return True

		if agechecked == 1 or agechecked == -1 :
			self.discrepancy = "mismatch"
			return True

		if agechecked > 1 or agechecked < -1 :
			self.discrepancy = "no_match"
			return True
		return None

	def check_record(self, dob) :
		"""Checks if the user has a date of birth in the database, and if the date of births match."""
		if AgeCalculations.check_date_of_birth(self.user_record, dob) is False :
			self.discrepancy = "dob_mismatch"
			return True
		return None

	def check_id_record(self) :
		"""Checks if the user is on the id list."""
		if id_check_info := AgeCalculations.id_check_or_id_verified(self.user) :
			self.discrepancy = "id_check"
			self.id_check_info = id_check_info


