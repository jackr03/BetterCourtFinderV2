import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from src.tasks import telegram_bot_task, court_updater_task

logging.basicConfig(
	level=logging.INFO,
	format='%(asctime)s [%(levelname)s] %(message)s',
	datefmt='%Y-%m-%d %H:%M:%S'
)

background_tasks = []


@asynccontextmanager
async def lifespan(app: FastAPI):
	# Startup code
	background_tasks.append(asyncio.create_task(court_updater_task()))
	background_tasks.append(asyncio.create_task(telegram_bot_task()))

	yield

	# Cleanup code
	for task in background_tasks:
		task.cancel()

	for task in background_tasks:
		try:
			await task
		except asyncio.CancelledError:
			pass


app = FastAPI(lifespan=lifespan)

if __name__ == '__main__':
	uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=True)
