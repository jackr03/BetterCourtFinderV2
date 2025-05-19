import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from starlette.responses import FileResponse

from src.tasks import telegram_bot_task, court_updater_task
from src.utils.constants import BADMINTON_COURTS_SCHEDULE_PATH

logging.basicConfig(
	level=logging.DEBUG,
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


@app.get('/badminton', response_class=FileResponse)
async def download_schedule() -> FileResponse:
	ics_file = Path(BADMINTON_COURTS_SCHEDULE_PATH)
	if ics_file.exists():
		return FileResponse(ics_file)
	raise HTTPException(status_code=404, detail='ICS file not found.')


if __name__ == '__main__':
	uvicorn.run('main:app', host='0.0.0.0', port=8000, reload=True)
