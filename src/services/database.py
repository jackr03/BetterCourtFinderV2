import sqlite3
from ..models import Court
from ..utils.constants import COURTS_DB_PATH


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