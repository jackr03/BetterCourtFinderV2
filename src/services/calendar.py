from datetime import datetime

from ics import Calendar, Event

from src.services.court_database import get_available_courts
from src.utils.constants import VENUE_MAP, BADMINTON_COURTS_SCHEDULE


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
