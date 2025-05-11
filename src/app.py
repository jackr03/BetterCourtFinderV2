import os
import sqlite3
from datetime import datetime

import requests

from src.models import Court

API_URL = 'https://better-admin.org.uk/api/activities/venue/{}/activity/{}/times'
SUGDEN_SLUG = 'sugden-sports-centre'
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

# TODO: Add better error handling
def fetch_courts() -> list[Court]:
	response = requests.get(API_URL.format(SUGDEN_SLUG, BADMINTON_40MIN),
							headers=HEADERS,
							params={'date': '2025-05-11'})
	response.raise_for_status()
	return [Court(**court) for court in response.json()['data']]

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

	cursor.execute('''
	INSERT OR IGNORE INTO courts (
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
	) VALUES (
	"test23",
	"sugden",
	"badminton",
	"badminton",
	"2025-05-11",
	"15:00",
	"13:00",
	"60",
	"£10.00",
	"5")
	''')

	conn.commit()
	conn.close()

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

if __name__ == '__main__':
	initialise_database()
	insert_courts(fetch_courts())
	print(get_available_courts())
