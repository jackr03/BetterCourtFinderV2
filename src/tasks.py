import asyncio
import logging
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from ics import Calendar, Event

from src.models import Court
from src.services.court_database import court_database
from src.services.court_fetcher import CourtFetcher
from src.telegram_bot.telegram_bot import TelegramBot
from src.utils.constants import VENUE_MAP, COURTS_ICS_PATH

load_dotenv()
logger = logging.getLogger(__name__)


# TODO: Mark when last updated
async def court_updater_task(interval: float = 300):
	court_fetcher = CourtFetcher()

	try:
		while True:
			logger.info('Updating court database')
			courts = court_fetcher.fetch_all()
			court_database.insert(courts)
			logger.info('Court database updated successfully')

			available_courts = court_database.get_all_available()
			_create_ics_file(available_courts)

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


def _create_ics_file(courts: list[Court]) -> None:
	logger.info('Creating ICS file')
	cal = Calendar()
	tz = ZoneInfo('Europe/London')

	for court in courts:
		event = Event()
		event.name = f'{court.name} ({VENUE_MAP[court.venue_slug]})'
		event.begin = datetime.combine(court.date, court.starts_at).replace(tzinfo=tz)
		event.end = datetime.combine(court.date, court.ends_at).replace(tzinfo=tz)
		event.location = VENUE_MAP[court.venue_slug]
		cal.events.add(event)

	with open(COURTS_ICS_PATH, 'w') as f:
		f.write(cal.serialize())
