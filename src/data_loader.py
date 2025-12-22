import pandas as pd
from config import RAW_DATA_FILE

class ShelterDataLoader:
    def __init__(self, filepath=RAW_DATA_FILE):
        self.filepath = filepath

    def load(self) -> pd.DataFrame:
        if not self.filepath.exists():
            raise FileNotFoundError(f"Data file not found: {self.filepath}")

        df = pd.read_csv(self.filepath)
        return df