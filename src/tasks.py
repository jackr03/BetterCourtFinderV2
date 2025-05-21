import asyncio
import logging
import os
import sys

from dotenv import load_dotenv

from src.services.court_updater import CourtUpdater
from src.telegram_bot.telegram_bot import TelegramBot

load_dotenv()
logger = logging.getLogger(__name__)


async def court_updater_task(interval: float = 300):
	try:
		while True:
			CourtUpdater().update()
			logger.info(f'Done, next update for courts in {interval} seconds')
			await asyncio.sleep(interval)
	except asyncio.CancelledError:
		logger.info('Court updater task cancelled')
		raise
	except Exception as e:
		logger.error(f'Error while updating courts: {e}')
		raise


async def telegram_bot_task():
	bot_token = os.getenv('BOT_TOKEN')
	if not bot_token:
		logger.error('BOT_TOKEN not set')
		sys.exit(1)

	bot = TelegramBot(bot_token)
	try:
		await bot.run()
	except asyncio.CancelledError:
		logger.info('Telegram bot task cancelled')
		raise
