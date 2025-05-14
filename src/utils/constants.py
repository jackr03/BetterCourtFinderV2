import os


VENUE_MAP = {
	'sugden-sports-centre': 'Sugden Sports Centre',
	'ardwick-sports-hall': 'Ardwick Sports Hall'
}

# Venues
SUGDEN_SPORTS_CENTRE = 'sugden-sports-centre'
ARDWICK_SPORTS_HALL = 'ardwick-sports-hall'

# Activities
BADMINTON_40MIN = 'badminton-40min'
BADMINTON_60MIN = 'badminton-60min'

# TODO: Make this relative to the project root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COURTS_DB_PATH = os.path.join(BASE_DIR, '../../data/courts.db')
BADMINTON_COURTS_SCHEDULE = os.path.join(BASE_DIR, '../../data/badminton_court_schedule.ics')