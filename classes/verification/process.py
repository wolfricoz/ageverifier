import logging

import discord
from discord.ext import commands

import databases.current
from classes.AgeCalculations import AgeCalculations
from classes.lobbyprocess import LobbyProcess
from classes.lobbytimers import LobbyTimers
from databases.enums.joinhistorystatus import JoinHistoryStatus
from databases.transactions.AgeRoleTransactions import AgeRoleTransactions
from databases.transactions.ConfigData import ConfigData
from databases.transactions.HistoryTransactions import JoinHistoryTransactions
from databases.transactions.UserTransactions import UserTransactions
from views.buttons.approvalbuttons import ApprovalButtons


class VerificationProcess :
	def __init__(self,
	             bot: commands.Bot,
	             member: discord.Member,
	             guild: discord.Guild,
	             day: str,
	             month: str,
	             year: str,
	             age: int | str,
	             reverify = False
	             ) :
		self.bot = bot
		self.member = member
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
		self.years = None,
		self.reverify = reverify

	async def verify(self) :
		try :
			# === Data validation starts here ===
			await self.load_data()
			if isinstance(self.age, str):
				self.age = int(self.age.strip())
			dob = await AgeCalculations.validate_user_info(self.member, self.age, f"{self.month}/{self.day}/{self.year}",
			                                               self.mod_channel)
			self.dob = dob
			agechecked, years = AgeCalculations.agechecker(self.age, dob)
			self.years = years
			self.age = int(self.age)
			# Check if member is underaged or below minimum age
			if self.check_underage(years):
				return self.discrepancy

			# Checks if the member is below the minimum age for the server.
			if self.check_minimum_age():
				return self.discrepancy

			# Check if users made any mistakes; prevent unnecessary ID checks.
			if self.check_typos(agechecked):
				return self.discrepancy

			# Checks if member has a date of birth in the database, and if the date of births match.
			if self.check_record(dob):
				return self.discrepancy

			# Checks if member is on the id list
			if self.check_id_record():
				return self.discrepancy

			# To be added: Check username for suspicious patterns.
			if self.discrepancy:
				return self.discrepancy
			# === Validation finished, we now start processing the member ===
			automatic_status = ConfigData().get_key_or_none(self.guild.id, "automatic_verification")
			if automatic_status and automatic_status == "enabled".upper() or self.reverify :
				await LobbyProcess.approve_user(self.guild, self.member, dob, self.age, "automatic_verification",
				                                reverify=self.reverify)
				return "Thank you for submitting your age and date of birth! You’ve been automatically verified and granted access."

			await AgeCalculations.check_history(self.guild.id, self.member, self.mod_channel)
			LobbyTimers().add_cooldown(self.guild.id, self.member.id, ConfigData().get_key_int_or_zero(self.guild.id, 'COOLDOWN'))
			approval_buttons = ApprovalButtons(age=self.age, dob=dob, user=self.member, reverify=self.reverify)
			await approval_buttons.send_message(self.guild, self.member, self.mod_channel)

			return "Your age and date of birth have been submitted successfully. A staff member will review your verification shortly to ensure everything checks out."

		except discord.Forbidden :
			self.error = "Ageverifier is missing permissions, please use `/config permissioncheck` to test permissions."
			logging.warning(f"Ageverifier is missing permissions, please use `/config permissioncheck` to test permissions.")
		except discord.NotFound :
			self.error = "Ageverifier could not fetch one of the channels, please use `/config view` and check if the channels still exist, and if ageverifier has permissions to view them."
			logging.warning(f"Ageverifier could not fetch one of the channels, please use `/config view` and check if the channels still exist, and if ageverifier has permissions to view them.")
		except ValueError:
			self.error = "Ageverifier could not validate your date of birth, please make sure it is in the format: mm/dd/yyyy"
		except Exception as e :

			self.error = e
			logging.warning(e)


	async def load_data(self) :
		"""Loads the data for the verification process and verifies it."""
		if self.age is None or self.day is None or self.month is None or self.year is None or self.member is None or self.guild is None :
			raise Exception("Missing data for verification: " +
			                f"age: {self.age}, day: {self.day}, month: {self.month}, year: {self.year}, member: {self.member}, guild: {self.guild}")
		self.user_record: databases.current.Users = UserTransactions().get_user(self.member.id)
		mod_lobby = ConfigData().get_key_int_or_zero(self.guild.id, "approval_channel")
		id_log = ConfigData().get_key_int_or_zero(self.guild.id, "verification_failure_log")
		if mod_lobby == 0 or id_log == 0 :
			raise Exception("Lobbymod or id_channel not set, inform the server staff to setup the server.")
		self.mod_channel = self.guild.get_channel(mod_lobby)
		self.id_channel = self.guild.get_channel(id_log)
		if self.id_channel is None :
			self.id_channel = await self.guild.fetch_channel(id_log)
		if self.mod_channel is None :
			self.mod_channel = await self.guild.fetch_channel(mod_lobby)

	def check_underage(self, years) :
		"""Checks if the member is underage."""
		if int(self.age) < 18 or int(years) < 18 :
			JoinHistoryTransactions().update(self.member.id, self.guild.id, JoinHistoryStatus.IDCHECK)
			self.discrepancy = "underage"
			return True
		return None

	def check_minimum_age(self) :
		"""Checks if the member is below the minimum age."""
		minimum_age = AgeRoleTransactions().get_minimum_age(self.guild.id)
		if minimum_age and self.age < minimum_age :
			self.discrepancy = "below_minimum_age"
			return True
		return None

	def check_typos(self, agechecked) :
		"""Checks if the member has any typos in their age."""
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
		"""Checks if the member has a date of birth in the database, and if the date of births match."""
		if AgeCalculations.check_date_of_birth(self.user_record, dob) is False :
			self.discrepancy = "dob_mismatch"
			return True
		return None

	def check_id_record(self) :
		"""Checks if the member is on the id list."""
		if id_check_info := AgeCalculations.id_check_or_id_verified(self.member) :
			self.discrepancy = "id_check"
			self.id_check_info = id_check_info


