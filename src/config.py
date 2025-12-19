from pathlib import Path

PROJECT_ROOT = Path(__file__).parent # folder that contains scr

DATA_DIR = PROJECT_ROOT / "data" # data folder
RAW_DATA_FILE = DATA_DIR / "raw" # raw data file

OUTPUT_DIR = PROJECT_ROOT / "output" # output folder
OUTPUT_DIR.mkdir(exist_ok=True) # create output folder if it doesn't exist yet

DB_PATH = DATA_DIR / "shelter.db" # database file