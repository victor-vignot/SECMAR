from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
DB_PATH = DATA_DIR / "db.sqlite"

CSV_PATHS = {
    "operations": RAW_DATA_DIR / "operations.csv",
    "flotteurs": RAW_DATA_DIR / "flotteurs.csv",
    "resultats_humain": RAW_DATA_DIR / "resultats_humain.csv",
    "operations_stats": RAW_DATA_DIR / "operations_stats.csv",
}
