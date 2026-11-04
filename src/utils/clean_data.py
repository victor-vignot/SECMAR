"""Construction des tables `raw` et `cleaned` de la base SQLite.

- `raw` : colonnes utiles des fichiers `operations.csv` et
  `operations_stats.csv`, jointes sur `operation_id`, valeurs inchangées
  (stockées en texte, telles que lues dans les CSV).
- `cleaned` : données typées, libellés corrigés et variables calculées une
  seule fois (durée, saison, gravité, familles, classes de vent et de mer,
  zone, distance à la côte fiable, positions fausses retirées).

Une copie compressée de la base (`data/db_initial.sqlite.xz`) est ensuite
créée : c'est elle qui est versionnée dans Git, car la base décompressée
dépasse 200 Mo.

Lancement : `uv run python -m src.utils.clean_data`
"""

import sqlite3
from contextlib import closing
from pathlib import Path

import pandas as pd
import shapely

from config import (
    CLASSES_MER,
    CLASSES_VENT,
    CORRECTIONS_CROSS,
    CORRECTIONS_DEPARTEMENT,
    CSV_PATHS,
    DATA_DIR,
    DB_ARCHIVE_PATH,
    DB_PATH,
    DISTANCE_INTERIEURE_MAX_KM,
    DUREE_MAX_HEURES,
    GRAVITES,
    SAISONS,
    TABLE_CLEANED,
    TABLE_RAW,
    TERRES_PATH,
    ZONE_INCONNUE,
    ZONE_OUTRE_MER,
    ZONES,
)
from src.utils.database import creer_archive
from src.utils.familles import EVENEMENTS_EVACUATION, famille_de
from src.utils.geographie import charger_terres, positions_a_terre

# Colonnes conservées dans chaque fichier source.
COLONNES_OPERATIONS = [
    "operation_id",
    "cross",
    "departement",
    "est_metropolitain",
    "evenement",
    "categorie_evenement",
    "zone_responsabilite",
    "latitude",
    "longitude",
    "vent_force",
    "mer_force",
    "date_heure_reception_alerte",
    "date_heure_fin_operation",
    "systeme_source",
]

COLONNES_STATS = [
    "operation_id",
    "annee",
    "mois",
    "prefecture_maritime",
    "distance_cote_milles_nautiques",
    "nombre_personnes_impliquees",
    "nombre_personnes_impliquees_sans_clandestins",
    "nombre_personnes_blessees",
    "nombre_personnes_decedees",
    "nombre_personnes_disparues",
    "nombre_personnes_secourues",
]

# Renommage des comptages pour des noms de colonnes plus courts.
RENOMMAGE_COMPTAGES = {
    "nombre_personnes_impliquees": "personnes_impliquees",
    "nombre_personnes_impliquees_sans_clandestins": (
        "personnes_impliquees_sans_clandestins"
    ),
    "nombre_personnes_blessees": "personnes_blessees",
    "nombre_personnes_decedees": "personnes_decedees",
    "nombre_personnes_disparues": "personnes_disparues",
    "nombre_personnes_secourues": "personnes_secourues",
}

# Types SQLite explicites : évite que le type soit deviné sur un échantillon.
TYPES_SQL_CLEANED = {
    "operation_id": "INTEGER PRIMARY KEY",
    "annee": "INTEGER",
    "mois": "INTEGER",
    "est_metropolitain": "INTEGER",
    "est_evacuation": "INTEGER",
    "latitude": "REAL",
    "longitude": "REAL",
    "vent_force": "INTEGER",
    "mer_force": "INTEGER",
    "duree_heures": "REAL",
    "distance_cote_mn": "REAL",
}

INDEX_CLEANED = ("annee", "cross", "famille")


def lire_csv_bruts(
    chemin_operations: Path = CSV_PATHS["operations"],
    chemin_stats: Path = CSV_PATHS["operations_stats"],
) -> pd.DataFrame:
    """Lit et joint les colonnes utiles des deux CSV, sans les modifier.

    Tout est lu en texte pour conserver exactement les valeurs sources.
    """
    operations = pd.read_csv(
        chemin_operations, usecols=COLONNES_OPERATIONS, dtype="string"
    )
    stats = pd.read_csv(chemin_stats, usecols=COLONNES_STATS, dtype="string")
    return operations.merge(stats, on="operation_id", how="inner")


def convertir_nombres(serie: pd.Series) -> pd.Series:
    """Convertit une colonne texte en nombres (valeurs invalides -> manquant)."""
    return pd.to_numeric(serie, errors="coerce")


def convertir_booleen(serie: pd.Series) -> pd.Series:
    """Convertit « True » / « False » en 1 / 0 (autres valeurs -> manquant)."""
    return serie.map({"True": 1, "False": 0}).astype("Int64")


def calculer_duree_heures(
    debut: pd.Series,
    fin: pd.Series,
    duree_max: float = DUREE_MAX_HEURES,
) -> pd.Series:
    """Calcule la durée d'opération en heures.

    Les durées nulles, négatives ou supérieures à `duree_max` sont mises à
    manquant : elles traduisent une saisie incomplète de l'heure de fin.
    """
    date_debut = pd.to_datetime(debut, errors="coerce", utc=True)
    date_fin = pd.to_datetime(fin, errors="coerce", utc=True)
    duree = (date_fin - date_debut).dt.total_seconds() / 3600
    return duree.where((duree > 0) & (duree <= duree_max))


def calculer_saison(mois: pd.Series) -> pd.Series:
    """Associe chaque numéro de mois à sa saison."""
    correspondance = {
        numero: saison
        for saison, numeros in SAISONS.items()
        for numero in numeros
    }
    return mois.map(correspondance)


def calculer_gravite(
    blesses: pd.Series,
    decedes: pd.Series,
    disparus: pd.Series,
) -> pd.Series:
    """Classe chaque opération selon ses conséquences humaines déclarées.

    Indicateur simple : décès ou disparus > blessés > aucune victime.
    """
    gravite = pd.Series(GRAVITES[0], index=blesses.index, dtype="object")
    gravite[blesses.fillna(0).gt(0).to_numpy(dtype=bool)] = GRAVITES[1]
    victimes_graves = decedes.fillna(0).gt(0) | disparus.fillna(0).gt(0)
    gravite[victimes_graves.to_numpy(dtype=bool)] = GRAVITES[2]
    return gravite


def classer_force(
    force: pd.Series,
    classes: dict[str, tuple[int, int]],
) -> pd.Series:
    """Range une force (vent ou mer) dans sa classe ; manquant si absente."""
    classe = pd.Series(pd.NA, index=force.index, dtype="object")
    for libelle, (borne_basse, borne_haute) in classes.items():
        dans_classe = force.between(borne_basse, borne_haute).fillna(False)
        classe[dans_classe] = libelle
    return classe


def calculer_zone(
    prefecture: pd.Series,
    est_metropolitain: pd.Series,
) -> pd.Series:
    """Détermine la façade maritime, ou « Outre-mer »."""
    zone = prefecture.map(ZONES).astype("object")
    zone[est_metropolitain.eq(0).fillna(False)] = ZONE_OUTRE_MER
    return zone.fillna(ZONE_INCONNUE)


def positions_invalides(
    latitude: pd.Series,
    longitude: pd.Series,
    terres: shapely.Geometry | None,
) -> pd.Series:
    """Repère les positions fausses : (0, 0) ou à terre loin de la côte.

    Sans trait de côte (`terres` à None), seules les positions (0, 0) sont
    repérées.
    """
    invalides = (latitude.eq(0) & longitude.eq(0)).fillna(False).to_numpy(dtype=bool)
    if terres is not None:
        # `|` crée un nouveau tableau : le tableau pandas peut être en lecture seule.
        invalides = invalides | positions_a_terre(
            latitude.to_numpy(dtype=float, na_value=float("nan")),
            longitude.to_numpy(dtype=float, na_value=float("nan")),
            terres,
            DISTANCE_INTERIEURE_MAX_KM,
        )
    return pd.Series(invalides, index=latitude.index)


def filtrer_distance_fiable(
    distance: pd.Series,
    position_valide: pd.Series,
    est_metropolitain: pd.Series,
) -> pd.Series:
    """Garde la distance à la côte seulement là où elle est fiable.

    L'audit a montré que la distance est cohérente en métropole, mais
    aberrante pour plusieurs territoires d'outre-mer (Polynésie, Martinique)
    et, bien sûr, pour les positions fausses.
    """
    fiable = est_metropolitain.eq(1).fillna(False) & position_valide
    return distance.where(fiable)


def nettoyer(raw: pd.DataFrame, terres: shapely.Geometry | None = None) -> pd.DataFrame:
    """Construit la table nettoyée à partir de la table brute.

    `terres` : terres émergées (voir `geographie.charger_terres`) servant à
    retirer les positions situées dans les terres.
    """
    cleaned = pd.DataFrame({"operation_id": convertir_nombres(raw["operation_id"])})

    colonnes_numeriques = [
        "annee",
        "mois",
        "latitude",
        "longitude",
        "vent_force",
        "mer_force",
        *RENOMMAGE_COMPTAGES,
    ]
    numeriques = {
        colonne: convertir_nombres(raw[colonne])
        for colonne in colonnes_numeriques
    }
    numeriques["est_metropolitain"] = convertir_booleen(
        raw["est_metropolitain"]
    )

    cleaned["annee"] = numeriques["annee"]
    cleaned["mois"] = numeriques["mois"]
    cleaned["saison"] = calculer_saison(numeriques["mois"])
    cleaned["cross"] = raw["cross"].replace(CORRECTIONS_CROSS)
    cleaned["departement"] = raw["departement"].replace(CORRECTIONS_DEPARTEMENT)
    cleaned["est_metropolitain"] = numeriques["est_metropolitain"]
    cleaned["zone"] = calculer_zone(
        raw["prefecture_maritime"], numeriques["est_metropolitain"]
    )
    cleaned["zone_responsabilite"] = raw["zone_responsabilite"]
    cleaned["systeme_source"] = raw["systeme_source"]
    cleaned["categorie_evenement"] = raw["categorie_evenement"]
    cleaned["evenement"] = raw["evenement"]
    cleaned["famille"] = raw["evenement"].astype("object").map(
        lambda valeur: famille_de(None if pd.isna(valeur) else valeur)
    )
    cleaned["est_evacuation"] = raw["evenement"].isin(
        EVENEMENTS_EVACUATION
    ).astype("int64")
    # Une position fausse est retirée : l'opération rejoint celles sans position.
    invalides = positions_invalides(numeriques["latitude"], numeriques["longitude"], terres)
    cleaned["latitude"] = numeriques["latitude"].mask(invalides)
    cleaned["longitude"] = numeriques["longitude"].mask(invalides)
    cleaned["vent_force"] = numeriques["vent_force"]
    cleaned["mer_force"] = numeriques["mer_force"]
    cleaned["classe_vent"] = classer_force(numeriques["vent_force"], CLASSES_VENT)
    cleaned["classe_mer"] = classer_force(numeriques["mer_force"], CLASSES_MER)
    cleaned["duree_heures"] = calculer_duree_heures(
        raw["date_heure_reception_alerte"], raw["date_heure_fin_operation"]
    )
    cleaned["distance_cote_mn"] = filtrer_distance_fiable(
        convertir_nombres(raw["distance_cote_milles_nautiques"]),
        ~invalides,
        numeriques["est_metropolitain"],
    )
    for source, cible in RENOMMAGE_COMPTAGES.items():
        cleaned[cible] = numeriques[source]
    cleaned["gravite"] = calculer_gravite(
        numeriques["nombre_personnes_blessees"],
        numeriques["nombre_personnes_decedees"],
        numeriques["nombre_personnes_disparues"],
    )
    # Les entiers pandas « nullables » restent des entiers dans SQLite.
    entiers = ["operation_id", "annee", "mois", "est_metropolitain",
               "vent_force", "mer_force", *RENOMMAGE_COMPTAGES.values()]
    cleaned[entiers] = cleaned[entiers].astype("Int64")
    return cleaned


def enregistrer_tables(
    raw: pd.DataFrame,
    cleaned: pd.DataFrame,
    chemin_base: Path = DB_PATH,
) -> None:
    """Écrit les tables `raw` et `cleaned` (remplacées si elles existent).

    Les autres tables éventuellement présentes dans la base ne sont pas
    touchées.
    """
    chemin_base.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(chemin_base)) as connexion:
        raw.to_sql(TABLE_RAW, connexion, if_exists="replace", index=False,
                   chunksize=50_000)
        cleaned.to_sql(TABLE_CLEANED, connexion, if_exists="replace",
                       index=False, chunksize=50_000, dtype=TYPES_SQL_CLEANED)
        for colonne in INDEX_CLEANED:
            connexion.execute(
                f"CREATE INDEX IF NOT EXISTS idx_{TABLE_CLEANED}_{colonne} "
                f"ON {TABLE_CLEANED} ({colonne})"
            )
        connexion.commit()


def main() -> None:
    """Construit `raw` et `cleaned` à partir des CSV de `data/raw/`."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    necessaires = [CSV_PATHS["operations"], CSV_PATHS["operations_stats"], TERRES_PATH]
    manquants = [str(chemin) for chemin in necessaires if not chemin.is_file()]
    if manquants:
        raise FileNotFoundError(
            "Fichiers manquants (lancer get_data.py) :\n" + "\n".join(manquants)
        )

    print("Lecture des CSV bruts...")
    raw = lire_csv_bruts()
    print(f"{len(raw):,} opérations lues. Nettoyage...".replace(",", " "))
    cleaned = nettoyer(raw, charger_terres(TERRES_PATH))
    print("Écriture des tables raw et cleaned...")
    enregistrer_tables(raw, cleaned)
    print(f"Base prête : {DB_PATH}")
    creer_archive()
    print(f"Archive versionnée mise à jour : {DB_ARCHIVE_PATH}")


if __name__ == "__main__":
    main()
