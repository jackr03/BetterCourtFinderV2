import logging
import sqlite3
from collections import defaultdict
from datetime import date

from ..models import Court
from ..utils.constants import COURTS_DB_PATH

logger = logging.getLogger(__name__)


class CourtDatabase:
	def __init__(self, db_path: str = COURTS_DB_PATH):
		self.db_path = db_path
		self._initialise()

	def _connect(self):
		return sqlite3.connect(self.db_path)

	# TODO: DB normalisation with venue and category slug (if needed)
	def _initialise(self):
		with self._connect() as conn:
			conn.execute('''
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

	# TODO: Add an audit log
	# TODO: Add indexes
	def insert(self, courts: list[Court]) -> None:
		with self._connect() as conn:
			cursor = conn.executemany('''
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
			''', [(
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
			) for court in courts
			])

			logger.info(f'Inserted/updated {cursor.rowcount} courts into the database')

	def get_all_available(self) -> list[Court]:
		with self._connect() as conn:
			rows = conn.execute('''
				SELECT * FROM courts
				WHERE spaces > 0
					AND date >= date('now')
					AND starts_at > time('now')
				ORDER BY date ASC, starts_at ASC
			''').fetchall()

			logger.info(f'Retrieved {len(rows)} available courts')
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

	def get_available_by_date(self, date: date) -> list[Court]:
		with self._connect() as conn:
			rows = conn.execute('''
				SELECT * FROM courts
				WHERE spaces > 0
					AND date = ?
					AND starts_at > time('now')
				ORDER BY starts_at ASC
			''', (date.strftime('%Y-%m-%d'),)).fetchall()

			logger.info(f'Retrieved {len(rows)} available courts for {date}')
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

	def get_available_by_time_range(self, time_range: tuple[int, int]) -> dict[date, list[Court]]:
		start, end = time_range

		with self._connect() as conn:
			rows = conn.execute('''
				SELECT * FROM courts
				WHERE spaces > 0
					AND date >= date('now')
					AND starts_at BETWEEN time(? || ':00:00') AND time(? || ':00:00')
				ORDER BY starts_at ASC
			''', (start, end)).fetchall()

			logger.info(f'Retrieved {len(rows)} available courts for time range {start}:00 - {end}:00')
			grouped = defaultdict(list)

			for row in rows:
				court = Court(
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
				grouped[date.fromisoformat(row[4])].append(court)

			return dict(grouped)


# TODO: Singleton pattern
court_database = CourtDatabase()
