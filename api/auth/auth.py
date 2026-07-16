import hmac
import ipaddress
import os

from dotenv import load_dotenv
from fastapi import HTTPException, Request, status

from project.whitelist import API_IP_WHITELIST

load_dotenv('.env')


class Auth() :
	"""
	"""
	_TOKEN = os.getenv("API_KEY")

	_request: Request = None
	_user_token: str | None = None

	def __init__(self, request: Request) :
		self._request = request

	async def verify(self) :
		"""
		This is the main authentication method, it will call all other methods and verify the user's login.
		"""
		# Get auth token from headers
		await self.get_auth_token()

		# Check auth token with .env
		await self.validate_auth_token()

		# Check IP whitelist (if set.)
		await self.check_ip_whitelist()

		# To ensure that no data is kept in the class, we clear it.
		await self.clear_data()

		# If everything matches, return true.
		return True

	# Support functions

	async def get_auth_token(self) -> None :
		"""
		Gets the auth token from the header
		"""
		self._user_token = self._request.headers.get("X-Auth-Token")

	async def validate_auth_token(self) -> bool :
		"""
		We check if the user's token matches the application's token.
		"""
		if not self._user_token :
			raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
		if not self._TOKEN :
			raise HTTPException(status_code=status.HTTP_412_PRECONDITION_FAILED)

		if hmac.compare_digest(self._user_token, self._TOKEN) :
			return True
		raise HTTPException(status_code=403)

	async def check_ip_whitelist(self) -> bool :
		"""
		We check if the user's IP address matches the application's IP whitelist.
		"""
		if not API_IP_WHITELIST :
			# If no whitelist is set, we just set it to true.
			return True
		client_ip = self._request.client.host

		try :
			# Check openVPN ranges
			vpn_subnet = ipaddress.ip_network('10.8.0.0/24')

			if ipaddress.ip_address(client_ip) in vpn_subnet :
				return True

			if client_ip in API_IP_WHITELIST :
				return True

		except ValueError :
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Malformed IP")
		raise HTTPException(status_code=403)

	async def clear_data(self) :
		"""
		Clears the data from the class to prevent it being used in other instances.
		"""
		self._request = None
		self._user_token = None

	def get_client_ip(self, request, trusted_proxy_count: int = 1) -> str :
		# X-Forwarded-For is appended to by each hop: "<client>, <proxy1>, <proxy2>".
		# The client's own value is the leftmost and fully spoofable; only the
		# rightmost `trusted_proxy_count` entries were added by proxies we control.
		xff = request.headers.get("x-forwarded-for")
		if not xff :
			# No proxy header at all — fall back to the socket peer.
			return request.client.host

		parts = [p.strip() for p in xff.split(",") if p.strip()]

		# Fewer hops than expected → header is short or spoofed; don't trust it.
		if len(parts) < trusted_proxy_count :
			return request.client.host

		# Leftmost entry of the trusted tail = the address our outermost proxy
		# actually saw on its incoming connection = the real client.
		return parts[len(parts) - trusted_proxy_count]