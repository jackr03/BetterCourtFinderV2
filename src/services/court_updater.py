import logging
from datetime import date, datetime
from typing import Optional
from zoneinfo import ZoneInfo

from ics import Event, Calendar

from src.models import Court
from src.services.court_database import CourtDatabase
from src.services.court_fetcher import CourtFetcher
from src.utils.constants import VENUE_MAP, COURTS_ICS_PATH

logger = logging.getLogger(__name__)


class CourtUpdater:
	_instance = None
	_initialised = False

	def __new__(cls):
		if cls._instance is None:
			logger.debug('Creating a new instance of CourtUpdater')
			cls._instance = super().__new__(cls)
		return cls._instance

	def __init__(self):
		if self._initialised:
			return
		self.court_fetcher = CourtFetcher()
		self.court_database = CourtDatabase()
		self.last_updated: Optional[date] = None
		self._initialised = True

	def update(self) -> None:
		logger.info('Updating court database')
		courts = self.court_fetcher.fetch_all()
		self.court_database.insert(courts)
		logger.info('Court database updated successfully')

		available_courts = self.court_database.get_all_available()
		self._create_ics_file(available_courts)
		self._set_last_updated()

	def get_last_updated(self) -> str:
		"""
		Returns the time that courts were last updated as a string in the format HH:MM:SS.
		"""
		if self.last_updated:
			return self.last_updated.strftime('%H:%M:%S')
		return 'never'

	def _set_last_updated(self) -> None:
		self.last_updated = datetime.now()
		logger.debug(f'Last updated time set to {self.get_last_updated()}')

	def _create_ics_file(self, courts: list[Court]) -> None:
		logger.info('Creating ICS file')
		cal = Calendar()
		tz = ZoneInfo('Europe/London')

		for court in courts:
			event = Event()
			event.name = f'{court.name} ({VENUE_MAP[court.venue_slug]})'
			event.begin = datetime.combine(court.date, court.starts_at).replace(tzinfo=tz)
			event.end = datetime.combine(court.date, court.ends_at).replace(tzinfo=tz)
			event.location = VENUE_MAP[court.venue_slug]
			event.description = f'Last updated: {self.get_last_updated()}'
			cal.events.add(event)

		with open(COURTS_ICS_PATH, 'w') as f:
			f.write(cal.serialize())
