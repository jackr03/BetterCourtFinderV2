import asyncio
import logging
import os
import sys
from datetime import datetime

from dotenv import load_dotenv
from ics import Calendar, Event

from src.models import Court
from src.services.court_database import court_database
from src.services.court_fetcher import CourtFetcher
from src.telegram_bot.telegram_bot import TelegramBot
from src.utils.constants import VENUE_MAP, BADMINTON_COURTS_SCHEDULE_PATH

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

			available_courts = court_database.get_all_available()
			create_ics_file(available_courts)
		except Exception as e:
			logger.error(f'Error while updating courts: {e}')

		logger.info(f'Done, next update for courts in {interval} seconds')
		await asyncio.sleep(interval)


async def telegram_bot_task():
	bot_token = os.getenv('BOT_TOKEN')
	if not bot_token:
		logger.error('BOT_TOKEN not set')
		sys.exit(1)

	bot = TelegramBot(bot_token)
	await bot.run()


def create_ics_file(courts: list[Court]) -> None:
	logger.info('Creating ICS file')
	cal = Calendar()

	for court in courts:
		event = Event()
		event.name = f'{court.name} ({VENUE_MAP[court.venue_slug]})'
		event.begin = datetime.combine(court.date, court.starts_at)
		event.end = datetime.combine(court.date, court.ends_at)
		event.location = VENUE_MAP[court.venue_slug]
		cal.events.add(event)

	with open(BADMINTON_COURTS_SCHEDULE_PATH, 'w') as f:
		f.write(cal.serialize())
