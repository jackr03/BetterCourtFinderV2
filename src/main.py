import os
import sqlite3
from concurrent.futures.thread import ThreadPoolExecutor
from http.client import HTTPException
from pathlib import Path

import requests

from datetime import date, datetime, timedelta

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi_utilities import repeat_every
from ics import Calendar, Event
from starlette.responses import FileResponse

from src.models import Court

# TODO: Move this stuff out
app = FastAPI()
router = APIRouter()

API_URL = 'https://better-admin.org.uk/api/activities/venue/{}/activity/{}/times'

VENUE_MAP = {
	'sugden-sports-centre': 'Sugden Sports Centre',
	'ardwick-sports-hall': 'Ardwick Sports Hall'
}
SUGDEN_SPORTS_CENTRE = 'sugden-sports-centre'
ARDWICK_SPORTS_HALL = 'ardwick-sports-hall'
BADMINTON_40MIN = 'badminton-40min'
BADMINTON_60MIN = 'badminton-60min'

HEADERS = {
	'accept': 'application/json',
	'origin': 'https://bookings.better.org.uk',
	'referer': 'https://bookings.better.org.uk/',
	'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0.1 Safari/605.1.15'
}

# TODO: Make this relative to the project root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COURTS_DB_PATH = os.path.join(BASE_DIR, '../data/courts.db')
BADMINTON_COURTS_SCHEDULE = os.path.join(BASE_DIR, '../data/badminton_court_schedule.ics')

# TODO: Move this to a different class
# TODO: Do some sort of DB normalisation with venue and category slug
def initialise_database() -> None:
	conn = sqlite3.connect(COURTS_DB_PATH)
	cursor = conn.cursor()

	cursor.execute('''
	CREATE TABLE IF NOT EXISTS courts (
		composite_key TEXT PRIMARY KEY,
		venue_slug TEXT,
		category_slug TEXT,
		name TEXT,
		date TEXT,
		starts_at TEXT,
		ends_at TEXT,
		duration TEXT,
		price TEXT,
		spaces INTEGER
	)
	''')

	conn.commit()
	conn.close()

# TODO: Add an audit log
# TODO: Add indexes
def insert_courts(courts: list[Court]) -> None:
	conn = sqlite3.connect(COURTS_DB_PATH)
	cursor = conn.cursor()

	insert_query = '''
	INSERT INTO courts (
		composite_key,
		venue_slug,
		category_slug,
		name,
		date,
		starts_at,
		ends_at,
		duration,
		price,
		spaces
	) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
	ON CONFLICT(composite_key)
	DO UPDATE SET
		spaces = excluded.spaces;
	'''

	data = [
		(
			court.composite_key,
			court.venue_slug,
			court.category_slug,
			court.name,
			court.date.strftime('%Y-%m-%d'),
			court.starts_at.strftime('%H:%M'),
			court.ends_at.strftime('%H:%M'),
			court.duration,
			court.price,
			court.spaces
		)
		for court in courts
	]

	cursor.executemany(insert_query, data)
	conn.commit()
	conn.close()

def get_available_courts() -> list[Court]:
	conn = sqlite3.connect(COURTS_DB_PATH)
	cursor = conn.cursor()

	cursor.execute('''
	SELECT * FROM courts
 	WHERE spaces > 0
		AND date >= date('now')
		AND starts_at > time('now')
	ORDER BY date ASC, starts_at ASC
	''')

	rows = cursor.fetchall()
	conn.close()

	return [
		Court(
			composite_key=row[0],
			venue_slug=row[1],
			category_slug=row[2],
			name=row[3],
			date=row[4],
			starts_at=row[5],
			ends_at=row[6],
			duration=row[7],
			price=row[8],
			spaces=row[9]
		)
		for row in rows
	]

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

# TODO: Make the mapping for venue_slug cleaner
def create_ics_file() -> None:
	courts = get_available_courts()

	cal = Calendar()

	for court in courts:
		event = Event()
		event.name = f'{court.name} ({VENUE_MAP[court.venue_slug]})'
		event.begin = datetime.combine(court.date, court.starts_at)
		event.end = datetime.combine(court.date, court.ends_at)
		event.location = VENUE_MAP[court.venue_slug]
		cal.events.add(event)

	with open(BADMINTON_COURTS_SCHEDULE, 'w') as f:
		f.write(cal.serialize())

@app.get('/badminton-schedule', response_class=FileResponse)
async def download_schedule() -> FileResponse:
	ics_file = Path(BADMINTON_COURTS_SCHEDULE)
	if ics_file.exists():
		return FileResponse(ics_file)
	raise HTTPException(status_code=404, detail='Schedule not found.')

@app.on_event('startup')
def initialise() -> None:
	print('Initialising...')
	initialise_database()
	insert_courts(fetch_all_courts())
	create_ics_file()

@repeat_every(seconds=600)
def update_schedule() -> None:
	print('Updating schedule...')
	insert_courts(fetch_all_courts())
	create_ics_file()

if __name__ == '__main__':
	initialise_database()
	# insert_courts(fetch_all_courts())
	# create_ics_file()
	# print(get_available_courts())
