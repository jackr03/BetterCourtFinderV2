from collections import defaultdict
from datetime import date

from src.models import Court


# TODO: Group by venue in the future
def format_court_availability(
		courts: list[Court],
		none_available_message: str
) -> str:
	courts_by_date = _group_courts_by_date(courts)

	if not any(courts_by_date.values()):
		return none_available_message

	sections = []

	for days, courts in sorted(courts_by_date.items()):
		lines = [f'✅ Courts available on {days.strftime("%A (%d/%m)")}:']
		for court in sorted(courts, key=lambda c: (c.starts_at, c.ends_at)):
			lines.append(
				f'🏸 {court.starts_at.strftime("%H:%M")} - {court.ends_at.strftime("%H:%M")} ({court.duration}), {court.spaces} space(s) left'
			)
		sections.append('\n'.join(lines))

	return '\n\n'.join(sections)


def _group_courts_by_date(courts: list[Court]) -> dict[date, list[Court]]:
	grouped = defaultdict(list)
	for court in courts:
		grouped[court.date].append(court)
	return dict(grouped)
