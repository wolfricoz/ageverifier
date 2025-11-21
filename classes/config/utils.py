from abc import ABC, abstractmethod


class ConfigUtils(ABC):

	@staticmethod
	@abstractmethod
	async def log_change():
		pass

