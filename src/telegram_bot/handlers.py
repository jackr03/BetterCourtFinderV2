import logging
from datetime import timedelta, datetime, date

from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from src.models import Court
from src.services.court_database import court_database

logger = logging.getLogger(__name__)
router = Router()


# TODO: Add some introduction to /start
@router.message(CommandStart())
async def start_command(message: Message):
	_log_command(message)
	await message.answer('Test')


# TODO: Get back button working
@router.message(Command('search'))
async def search_command(message: Message):
	_log_command(message)
	await message.answer(
		'Search by...',
		reply_markup=_get_search_keyboard()
	)


@router.callback_query(lambda c: c.data == 'search')
async def search_callback(callback_query: CallbackQuery):
	_log_callback_query(callback_query)
	await callback_query.message.edit_text(
		'Search by...',
		reply_markup=_get_search_keyboard()
	)


@router.callback_query(lambda c: c.data == 'search_by_date')
async def search_by_date_callback(callback_query: CallbackQuery):
	_log_callback_query(callback_query)

	dates = [(datetime.today() + timedelta(days=i)).date() for i in range(6)]

	keyboard_buttons = [
		[InlineKeyboardButton(
			text=f'📅 {d.strftime("%A (%d/%m)")}',
			callback_data=f'search_by_date_{d.isoformat()}'
		)] for d in dates
	]

	keyboard_buttons.append([_get_back_button('search')])

	await callback_query.message.edit_text(
		'Select a date:',
		reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
	)


@router.callback_query(lambda c: c.data.startswith('search_by_date_'))
async def search_by_date_selected_callback(callback_query: CallbackQuery):
	_log_callback_query(callback_query)
	prefix = 'search_by_date_'
	date = datetime.fromisoformat(callback_query.data[len(prefix):])
	courts = court_database.get_available_by_date(date)

	keyboard_buttons = [
		[_get_back_button('search_by_date')]
	]

	await callback_query.message.edit_text(
		_format_availability(date, courts),
		reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
	)


@router.callback_query(lambda c: c.data == 'search_by_time')
async def search_by_time_callback(callback_query: CallbackQuery):
	_log_callback_query(callback_query)

	keyboard_buttons = [
		[InlineKeyboardButton(
			text='🌅 Morning (07:00 - 12:00)',
			callback_data='search_by_time_morning'
		)],
		[InlineKeyboardButton(
			text='☀️ Afternoon (12:00 - 17:00',
			callback_data='search_by_time_afternoon'
		)],
		[InlineKeyboardButton(
			text='🌙 Evening (17:00 - 22:00)',
			callback_data='search_by_time_evening'
		)],
		[_get_back_button('search')]
	]

	await callback_query.message.edit_text(
		'Select a time:',
		reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
	)


@router.callback_query(lambda c: c.data.startswith('search_by_time_'))
async def search_by_time_selected_callback(callback_query: CallbackQuery):
	_log_callback_query(callback_query)
	prefix = 'search_by_time_'
	time_range = {
		'morning': (7, 12),
		'afternoon': (12, 17),
		'evening': (17, 22)
	}[callback_query.data[len(prefix):]]

	courts = court_database.get_available_by_time_range(time_range)

	keyboard_buttons = [
		[_get_back_button('search_by_time')]
	]

	await callback_query.message.edit_text(
		_format_multiple_days_availability(time_range, courts),
		reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
	)


def _get_search_keyboard() -> InlineKeyboardMarkup:
	return InlineKeyboardMarkup(inline_keyboard=[
		[InlineKeyboardButton(
			text='📅 Date',
			callback_data='search_by_date'
		)],
		[InlineKeyboardButton(
			text='⏰ Time',
			callback_data='search_by_time'
		)]
	])


def _get_back_button(callback_data: str) -> InlineKeyboardButton:
	return InlineKeyboardButton(
		text='⬅️ Back',
		callback_data=callback_data
	)


# TODO: Group by venue
def _format_availability(date: date, courts: list[Court]) -> str:
	if not courts:
		return f'❌ No courts available on {date.strftime("%A (%d/%m)")}.'

	lines = [f'✅ Courts available on {date.strftime("%A (%d/%m)")}:', '']

	for court in courts:
		lines.append(
			f'️🏸 {court.starts_at.strftime('%H:%M')} - {court.ends_at.strftime('%H:%M')} ({court.duration}), {court.spaces} space(s) left')

	return '\n'.join(lines)


def _format_multiple_days_availability(time_range: tuple[int, int], courts_by_date: dict[date, list[Court]]) -> str:
	if not any(courts_by_date.values()):
		return f'❌ No courts available for the time range {time_range[0]}:00 - {time_range[1]}:00.'

	sections = []

	for day, courts in sorted(courts_by_date.items()):
		if not courts:
			continue

		lines = [f'✅ Courts available on {day.strftime("%A (%d/%m)")}:', '']
		for court in courts:
			lines.append(
				f'🏸 {court.starts_at.strftime("%H:%M")} - {court.ends_at.strftime("%H:%M")} ({court.duration}), {court.spaces} space(s) left'
			)
		sections.append('\n'.join(lines))

	return '\n\n'.join(sections)


def _log_command(message: Message):
	logger.debug(f'Received command: {message.text} from user {message.from_user.id}')


def _log_callback_query(callback_query: CallbackQuery):
	logger.debug(f'Received callback query: {callback_query.data} from user {callback_query.from_user.id}')
