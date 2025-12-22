from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1] # folder that contains src, so PROJECT_ROOT is animal-shelter-dashboard/

DATA_DIR = PROJECT_ROOT / "data" # data folder
RAW_DATA_FILE = DATA_DIR / "animal-shelter-intakes-and-outcomes.csv" # raw data file

DB_PATH = DATA_DIR / "shelter.db" # database file