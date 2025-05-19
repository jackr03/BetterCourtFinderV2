import asyncio
import logging
from collections import defaultdict

from aiogram import Bot, Dispatcher

from src.models import Court
from src.services.court_database import court_database
from src.telegram_bot.bot_config import bot_config
from src.telegram_bot.handlers import router

logger = logging.getLogger(__name__)


class TelegramBot:
	def __init__(self, bot_token: str):
		self.bot = Bot(bot_token)
		self.dp = Dispatcher()
		self.dp.include_router(router)
		self.config = bot_config

		logger.info('Building initial court availability cache')
		self.cache = court_database.get_all_available()

	async def run(self):
		# Ignore outdated messages upon startup
		await self.bot.delete_webhook(drop_pending_updates=True)
		logger.info("Bot initialised")

		asyncio.create_task(self._availability_monitor_task())
		await self.dp.start_polling(self.bot)

	async def _availability_monitor_task(self):
		while True:
			await asyncio.sleep(self.config.get('polling_interval'))
			logger.info('Running check for any changes in court availability')

			new_court_availability = court_database.get_all_available()

			now_available = set(self.cache) - set(new_court_availability)
			now_unavailable = set(new_court_availability) - set(self.cache)

			if not now_available and not now_unavailable:
				logger.info('No changes in court availability, no notification will be sent')
				continue
			elif now_available:
				logger.debug(f'Change in courts now available: {now_available}')
			elif now_unavailable:
				logger.debug(f'Change in courts now unavailable: {now_unavailable}')

			self.cache = new_court_availability

			logger.info('Notifying users of court availability changes')
			await self._notify_users(list(now_available), list(now_unavailable))

			logger.info(f'Done, next check for court availability in {self.config.get('polling_interval')} seconds')

	async def _notify_users(self, now_available: list[Court], now_unavailable: list[Court]):
		notify_list = self.config.get_notify_list()
		if not notify_list:
			logger.info('No users to notify')
			return

		for user_id in notify_list:
			if now_available:
				await self.bot.send_message(
					user_id,
					self._format_court_availability(f'✅ Now available:', now_available)
				)

			if now_unavailable:
				await self.bot.send_message(
					user_id,
					self._format_court_availability(f'❌ Now unavailable:', now_unavailable)
				)

	def _format_court_availability(self, header: str, courts: list[Court]) -> str:
		courts_by_date = defaultdict(list)
		for court in courts:
			courts_by_date[court.date].append(court)

		sections = [header, '']

		for day, courts in sorted(courts_by_date.items()):
			if not courts:
				continue

			lines = [f'📅 {day.strftime("%A (%d/%m)")}:']
			for court in courts:
				lines.append(
					f'🏸 {court.starts_at.strftime("%H:%M")} - {court.ends_at.strftime("%H:%M")} ({court.duration})'
				)
			sections.append('\n'.join(lines))

		return '\n\n'.join(sections)
