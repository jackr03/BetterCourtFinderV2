import logging

import toml

from src.utils.constants import BOT_CONFIG_PATH

# TODO: Use proper logging

logger = logging.getLogger(__name__)


class BotConfig:
	DEFAULT_CONFIG = {
		'settings': {
			'polling_interval': 300,
			'notify_list': set()
		}
	}

	def __init__(self):
		self.config_path = BOT_CONFIG_PATH
		self.config = self._load()

	def _load(self) -> dict:
		logger.debug(f'Attempting to load config from {self.config_path}')
		try:
			with open(self.config_path, 'r') as f:
				logger.info(f'Config loaded from {self.config_path}')
				return toml.load(f)
		# File not found, return the default config
		except FileNotFoundError:
			logger.info(f'No config file found at {self.config_path}, using defaults')
			return self.DEFAULT_CONFIG.copy()

	def _save(self):
		with open(self.config_path, 'w') as f:
			toml.dump(self.config, f)
			logger.info(f'Config saved to {self.config_path}')

	def get(self, key: str):
		return self.config.get('settings').get(key)

	def set(self, key: str, value):
		self.config['settings'][key] = value
		self._save()

	def get_notify_list(self) -> set:
		return set(self.get('notify_list'))

	def add_to_notify_list(self, user_id: int):
		notify_list = self.get_notify_list()
		notify_list.add(user_id)
		self.set('notify_list', list(notify_list))
		logger.info(f'Added user {user_id} to notify list')

	def remove_from_notify_list(self, user_id: int):
		notify_list = self.get_notify_list()
		notify_list.remove(user_id)
		self.set('notify_list', list(notify_list))
		logger.info(f'Removed user {user_id} from notify list')


bot_config = BotConfig()
