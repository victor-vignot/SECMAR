
from pathlib import Path

# Définit le dossier principal du projet.
BASE_DIR = Path(__file__).resolve().parent

# Définit les chemins des données.
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
DB_PATH = DATA_DIR / "db.sqlite"

# Définit les tables présentes dans la base SQLite.
TABLE_OPERATIONS = "raw_operations"
TABLE_FLOTTEURS = "raw_flotteurs"
TABLE_RESULTATS_HUMAIN = "raw_resultats_humain"
TABLE_OPERATIONS_STATS = "raw_operations_stats"

# Définit les noms des colonnes utilisées par le dashboard.
ZONE_COLUMN = "cross"
EVENT_COLUMN = "categorie_evenement"
YEAR_COLUMN = "annee"

# Définit la période d'analyse du dashboard.
ANNEE_MIN = 2005
ANNEE_MAX = 2025

# Limite le nombre de points affichés sur la carte.
MAX_POINTS_CARTE = 30000

# Indique où se trouvent les fichiers CSV téléchargés.
CSV_PATHS = {
    "operations": RAW_DATA_DIR / "operations.csv",
    "flotteurs": RAW_DATA_DIR / "flotteurs.csv",
    "resultats_humain": RAW_DATA_DIR / "resultats_humain.csv",
    "operations_stats": RAW_DATA_DIR / "operations_stats.csv",
}
