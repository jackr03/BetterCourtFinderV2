import asyncio
import logging
import os
import sys

from dotenv import load_dotenv

from src.services.court_database import court_database
from src.services.court_fetcher import CourtFetcher
from src.telegram_bot.telegram_bot import TelegramBot

load_dotenv()
logger = logging.getLogger(__name__)


# TODO: Mark when last updated
async def court_updater_task(interval: float = 300):
	court_fetcher = CourtFetcher()

	while True:
		try:
			logger.info('Updating court database')
			courts = court_fetcher.fetch_all()
			court_database.insert(courts)
			logger.info('Court database updated successfully')
		except Exception as e:
			logger.error(f'Error while updating courts: {e}')

		logger.info(f'Court updater sleeping for {interval} seconds')
		await asyncio.sleep(interval)


async def telegram_bot_task():
	bot_token = os.getenv('BOT_TOKEN')
	if not bot_token:
		logger.error('BOT_TOKEN not set')
		sys.exit(1)

	bot = TelegramBot(bot_token)
	await bot.run()
