from concurrent.futures import ThreadPoolExecutor

import requests

from datetime import datetime, date, timedelta
from ..models import Court
from ..utils.constants import SUGDEN_SPORTS_CENTRE, BADMINTON_40MIN, BADMINTON_60MIN

API_URL = 'https://better-admin.org.uk/api/activities/venue/{}/activity/{}/times'

HEADERS = {
	'accept': 'application/json',
	'origin': 'https://bookings.better.org.uk',
	'referer': 'https://bookings.better.org.uk/',
	'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0.1 Safari/605.1.15'
}

# TODO: Add better error handling
def fetch_courts(venue_slug: str,
				 category_slug: str,
				 date: date) -> list[Court]:
	print(f'Getting courts for {category_slug} at {venue_slug} on {date}')
	response = requests.get(API_URL.format(venue_slug, category_slug),
							headers=HEADERS,
							params={'date': date.isoformat()})
	response.raise_for_status()
	data = response.json()['data']

	# The response can come in two forms - either a dictionary or a list
	court_list = list(data.values())\
		if isinstance(data, dict)\
		else data

	return [Court(**court) for court in court_list]

# TODO: Make more modular for other courts
def fetch_all_courts() -> list[Court]:
	dates = [(datetime.today() + timedelta(days=i)).date() for i in range(6)]
	courts = []

	def fetch_for_date_and_category(date, category_slug):
		return fetch_courts(SUGDEN_SPORTS_CENTRE, category_slug, date)

	with ThreadPoolExecutor(max_workers=6) as executor:
		tasks = [(date, category) for date in dates for category in [BADMINTON_40MIN, BADMINTON_60MIN]]
		results = executor.map(lambda p: fetch_for_date_and_category(*p), tasks)

	for result in results:
		courts.extend(result)

	return courts