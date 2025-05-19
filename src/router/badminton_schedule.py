from pathlib import Path

from fastapi import FastAPI, APIRouter, HTTPException
from fastapi_utilities import repeat_every
from starlette.responses import FileResponse

from src.services.court_database import initialise_database, insert_courts
from src.services.court_fetcher import fetch_all_courts
from src.utils.constants import BADMINTON_COURTS_SCHEDULE

# TODO: Move this stuff out
app = FastAPI()
router = APIRouter()


@app.get('/badminton-schedule', response_class=FileResponse)
async def download_schedule() -> FileResponse:
	ics_file = Path(BADMINTON_COURTS_SCHEDULE)
	if ics_file.exists():
		return FileResponse(ics_file)
	raise HTTPException(status_code=404, detail='Schedule not found.')


@app.on_event('startup')
def initialise() -> None:
	print('Initialising...')
	initialise_database()
	insert_courts(fetch_all_courts())
	create_ics_file()


@repeat_every(seconds=600)
def update_schedule() -> None:
	print('Updating schedule...')
	insert_courts(fetch_all_courts())
	create_ics_file()
