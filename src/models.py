from datetime import time, date

from pydantic import BaseModel, field_validator


class Court(BaseModel):
	composite_key: str
	venue_slug: str
	category_slug: str
	name: str
	
	date: date
	starts_at: time
	ends_at: time
	duration: str
	
	price: str
	spaces: int

	@field_validator('date', mode='before')
	@classmethod
	def parse_court_date(cls, v) -> date:
		return date.fromisoformat(v)

	@field_validator('starts_at', 'ends_at', mode='before')
	@classmethod
	def parse_times(cls, v) -> time:
		return time.fromisoformat(v['format_24_hour'])\
			if isinstance(v, dict)\
			else time.fromisoformat(v)

	@field_validator('price', mode='before')
	@classmethod
	def parse_price(cls, v) -> str:
		return v['formatted_amount']\
			if isinstance(v, dict)\
			else v
