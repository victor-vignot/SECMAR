"""Configuration centrale du projet SECMAR.

Toutes les décisions modifiables (période, seuils, classes, chemins) sont
regroupées ici afin de pouvoir les ajuster sans toucher au reste du code.
"""

from pathlib import Path

# --- Chemins -----------------------------------------------------------------

# Définit le dossier principal du projet.
BASE_DIR = Path(__file__).resolve().parent

# Définit les chemins des données.
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
DB_PATH = DATA_DIR / "db.sqlite"

# Copie compressée de la base, versionnée dans Git (la base fait ~230 Mo).
# Elle permet de lancer le tableau de bord sans connexion internet.
DB_ARCHIVE_PATH = DATA_DIR / "db_initial.sqlite.xz"

# Indique où se trouvent les fichiers CSV téléchargés.
CSV_PATHS = {
    "operations": RAW_DATA_DIR / "operations.csv",
    "flotteurs": RAW_DATA_DIR / "flotteurs.csv",
    "resultats_humain": RAW_DATA_DIR / "resultats_humain.csv",
    "operations_stats": RAW_DATA_DIR / "operations_stats.csv",
}

# --- Tables SQLite -------------------------------------------------------------

# Tables demandées par la consigne : données brutes et données nettoyées.
TABLE_RAW = "raw"
TABLE_CLEANED = "cleaned"

# --- Période d'analyse ----------------------------------------------------------

# Bornes du curseur de période. 2026 est exclue car l'année est incomplète.
ANNEE_MIN = 1985
ANNEE_MAX = 2025

# Période sélectionnée à l'ouverture du tableau de bord.
ANNEE_DEBUT_DEFAUT = 2005
ANNEE_FIN_DEFAUT = 2025

# --- Seuils de nettoyage -------------------------------------------------------

# Au-delà de cette durée, l'heure de fin est jugée peu fiable.
DUREE_MAX_HEURES = 72.0

# Borne haute de l'histogramme de distance à la côte (milles nautiques).
DISTANCE_MAX_HISTOGRAMME_MN = 30.0

# Largeur d'une classe de l'histogramme de distance (milles nautiques).
LARGEUR_CLASSE_DISTANCE_MN = 0.5

# Nombre minimal d'opérations pour afficher une case de tableau croisé.
EFFECTIF_MINIMAL = 30

# Limite le nombre de points affichés sur la carte.
MAX_POINTS_CARTE = 20000

# --- Classes ordonnées ------------------------------------------------------------

# Regroupement de l'échelle de Beaufort (vent) pour éviter les cases vides.
CLASSES_VENT = {
    "0-3 faible": (0, 3),
    "4-5 modéré": (4, 5),
    "6-7 fort": (6, 7),
    "8+ tempête": (8, 12),
}

# Regroupement de l'échelle de Douglas (état de la mer).
CLASSES_MER = {
    "0-2 calme": (0, 2),
    "3 agitée": (3, 3),
    "4 forte": (4, 4),
    "5+ très forte": (5, 9),
}

# Saisons météorologiques de l'hémisphère nord.
SAISONS = {
    "Hiver": (12, 1, 2),
    "Printemps": (3, 4, 5),
    "Été": (6, 7, 8),
    "Automne": (9, 10, 11),
}

# Classes de gravité, de la moins grave à la plus grave.
GRAVITES = [
    "Aucun blessé, décès ou disparu",
    "Blessés",
    "Décès ou disparus",
]

# Libellés des façades maritimes (zone géographique).
ZONES = {
    "manche": "Manche - mer du Nord",
    "atlantique": "Atlantique",
    "mediterranee": "Méditerranée",
}
ZONE_OUTRE_MER = "Outre-mer"
ZONE_INCONNUE = "Non renseignée"

# Corrections de libellés incohérents dans les données sources.
CORRECTIONS_CROSS = {"Adge": "Agde"}
CORRECTIONS_DEPARTEMENT = {"Réunion": "La Réunion"}

# Valeur « tout sélectionner » des listes déroulantes.
VALEUR_TOUTES = "toutes"


# --- Compatibilité temporaire (jour 1 uniquement) -----------------------------
# L'ancien code (queries.py, clean_data.py) utilise encore ces noms.
# Ce bloc disparaît au jour 2, quand ces fichiers passent à la table `cleaned`.
TABLE_OPERATIONS = "raw_operations"
TABLE_FLOTTEURS = "raw_flotteurs"
TABLE_RESULTATS_HUMAIN = "raw_resultats_humain"
TABLE_OPERATIONS_STATS = "raw_operations_stats"
ZONE_COLUMN = "cross"
EVENT_COLUMN = "categorie_evenement"
YEAR_COLUMN = "annee"
