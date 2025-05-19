import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, date, timedelta

from requests import Session

from ..models import Court
from ..utils.constants import SUGDEN_SPORTS_CENTRE, BADMINTON_40MIN, BADMINTON_60MIN

logger = logging.getLogger(__name__)


class CourtFetcher:
	API_URL = 'https://better-admin.org.uk/api/activities/venue/{venue_slug}/activity/{category_slug}/times'
	HEADERS = {
		'accept': 'application/json',
		'origin': 'https://bookings.better.org.uk',
		'referer': 'https://bookings.better.org.uk/',
		'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0.1 Safari/605.1.15'
	}

	def __init__(
			self,
			venue_slug: str = SUGDEN_SPORTS_CENTRE,
			category_slugs: list[str] = (BADMINTON_40MIN, BADMINTON_60MIN),
	):
		self.venue_slug = venue_slug
		self.category_slugs = category_slugs
		self.session = Session()
		self.session.headers.update(self.HEADERS)

	def fetch_all(self) -> list[Court]:
		logger.info('Fetching all courts')
		# Check the next 6 days
		dates = [(datetime.today() + timedelta(days=i)).date() for i in range(6)]
		args = [(category_slug, date) for date in dates for category_slug in self.category_slugs]
		courts: list[Court] = []

		def fetch_for_category_and_date(arg):
			category_slug, date = arg
			return self._fetch_for(category_slug, date)

		with ThreadPoolExecutor(max_workers=6) as executor:
			for batch in executor.map(fetch_for_category_and_date, args):
				courts.extend(batch)

		return courts

	def _fetch_for(self, category_slug: str, date: date) -> list[Court]:
		logger.debug(f'Fetching courts for {category_slug} at {self.venue_slug} on {date}')
		try:
			response = self.session.get(
				self.API_URL.format(venue_slug=self.venue_slug,
									category_slug=category_slug),
				params={'date': date.isoformat()}
			)
			response.raise_for_status()
			data = response.json()['data']

			# The response can come in two forms - either a dictionary or a list
			court_list = list(data.values()) if isinstance(data, dict) else data
			return [Court(**court) for court in court_list]
		except Exception as e:
			logger.error(f'Error fetching courts for {category_slug} at {self.venue_slug} on {date}: {e}')
			raise
