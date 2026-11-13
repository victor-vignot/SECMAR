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

# Trait de côte mondial Natural Earth 1:10 000 000 (domaine public), utilisé
# pour repérer les positions situées dans les terres.
TERRES_PATH = RAW_DATA_DIR / "ne_10m_land.geojson"

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
# Mois sélectionnés par défaut : toute l'année.
MOIS_DEBUT_DEFAUT = 1
MOIS_FIN_DEFAUT = 12

# --- Seuils de nettoyage -------------------------------------------------------

# Au-delà de cette durée, l'heure de fin est jugée peu fiable.
DUREE_MAX_HEURES = 72.0

# Borne haute de l'histogramme de distance à la côte (milles nautiques).
DISTANCE_MAX_HISTOGRAMME_MN = 30.0

# Largeur d'une classe de l'histogramme de distance (milles nautiques).
LARGEUR_CLASSE_DISTANCE_MN = 0.5

# Une position à terre à plus de cette distance de la côte est jugée fausse
# (position par défaut) : elle est retirée, comme les positions (0, 0).
DISTANCE_INTERIEURE_MAX_KM = 5.0

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

# Noms des mois : abrégés pour les axes, complets pour les messages.
NOMS_MOIS = {
    1: "janv.", 2: "févr.", 3: "mars", 4: "avr.", 5: "mai", 6: "juin",
    7: "juil.", 8: "août", 9: "sept.", 10: "oct.", 11: "nov.", 12: "déc.",
}
NOMS_MOIS_LONGS = {
    1: "janvier", 2: "février", 3: "mars", 4: "avril", 5: "mai", 6: "juin",
    7: "juillet", 8: "août", 9: "septembre", 10: "octobre", 11: "novembre", 12: "décembre",
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

# Ruptures dans la façon d'enregistrer les opérations : (début, fin, explication).
# Les comparaisons dans le temps qui les traversent sont à lire avec prudence.
RUPTURES_SAISIE = [
    (2009, 2010, "les « difficultés de manœuvre » deviennent des avaries de propulsion"),
    (2019, 2021, "passage du logiciel SECMARweb au logiciel SEAMIS"),
]

# Valeur « tout sélectionner » des listes déroulantes.
VALEUR_TOUTES = "toutes"
