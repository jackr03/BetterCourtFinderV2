import logging

from aiogram import Bot, Dispatcher

from src.telegram_bot.bot_config import BotConfig
from src.telegram_bot.handlers import router

logger = logging.getLogger(__name__)


class TelegramBot:
	def __init__(self, bot_token: str):
		self.bot = Bot(bot_token)
		self.dp = Dispatcher()
		self.dp.include_router(router)
		self.config = BotConfig()

	async def run(self):
		# Ignore outdated messages upon startup
		await self.bot.delete_webhook(drop_pending_updates=True)
		logger.info("Starting bot...")
		await self.dp.start_polling(self.bot)
