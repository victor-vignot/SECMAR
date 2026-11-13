"""Requêtes SQLite utilisées par le tableau de bord.

Une seule requête filtrée lit la table `cleaned` ; son résultat est mis en
cache pour que tous les graphiques d'un même filtrage le réutilisent sans
relire la base.
"""

from dataclasses import dataclass
from functools import lru_cache

import pandas as pd

from config import (
    ANNEE_DEBUT_DEFAUT,
    ANNEE_FIN_DEFAUT,
    CLASSES_MER,
    CLASSES_VENT,
    GRAVITES,
    MOIS_DEBUT_DEFAUT,
    MOIS_FIN_DEFAUT,
    SAISONS,
    TABLE_CLEANED,
    VALEUR_TOUTES,
)
from src.utils.database import ouvrir_connexion
from src.utils.familles import ORDRE_FAMILLES

# Valeurs du filtre de périmètre géographique.
PERIMETRE_TOUT = VALEUR_TOUTES
PERIMETRE_METROPOLE = "metropole"
PERIMETRE_OUTRE_MER = "outre-mer"

# Colonnes lues pour le tableau de bord (les autres restent dans la base).
COLONNES_DASHBOARD = [
    "operation_id",
    "annee",
    "mois",
    "saison",
    "cross",
    "departement",
    "est_metropolitain",
    "zone",
    "famille",
    "evenement",
    "est_evacuation",
    "latitude",
    "longitude",
    "vent_force",
    "mer_force",
    "classe_vent",
    "classe_mer",
    "duree_heures",
    "distance_cote_mn",
    "personnes_impliquees",
    "personnes_impliquees_sans_clandestins",
    "personnes_blessees",
    "personnes_decedees",
    "personnes_disparues",
    "personnes_secourues",
    "gravite",
]

# Ordre logique des catégories, utilisé par les graphiques.
ORDRES_CATEGORIES: dict[str, list[str]] = {
    "famille": ORDRE_FAMILLES,
    "classe_vent": list(CLASSES_VENT),
    "classe_mer": list(CLASSES_MER),
    "saison": list(SAISONS),
    "gravite": GRAVITES,
}


@dataclass(frozen=True)
class Filtres:
    """Valeurs sélectionnées dans le panneau de filtres."""

    annee_debut: int = ANNEE_DEBUT_DEFAUT
    annee_fin: int = ANNEE_FIN_DEFAUT
    cross: str = VALEUR_TOUTES
    famille: str = VALEUR_TOUTES
    perimetre: str = PERIMETRE_TOUT
    mois_debut: int = MOIS_DEBUT_DEFAUT
    mois_fin: int = MOIS_FIN_DEFAUT


def charger_options_filtres() -> tuple[list[str], list[str]]:
    """Retourne les CROSS et les familles disponibles dans la base."""
    with ouvrir_connexion() as connexion:
        cross = pd.read_sql_query(
            f"SELECT DISTINCT cross FROM {TABLE_CLEANED} "
            "WHERE cross IS NOT NULL ORDER BY cross",
            connexion,
        )["cross"].tolist()
        familles_presentes = set(
            pd.read_sql_query(
                f"SELECT DISTINCT famille FROM {TABLE_CLEANED}", connexion
            )["famille"]
        )
    familles = [f for f in ORDRE_FAMILLES if f in familles_presentes]
    return cross, familles


def construire_requete(filtres: Filtres) -> tuple[str, list[int | str]]:
    """Construit la requête SQL paramétrée correspondant aux filtres."""
    requete = (
        f"SELECT {', '.join(COLONNES_DASHBOARD)} FROM {TABLE_CLEANED} "
        "WHERE annee BETWEEN ? AND ?"
    )
    parametres: list[int | str] = [
        int(filtres.annee_debut),
        int(filtres.annee_fin),
    ]
    if filtres.cross != VALEUR_TOUTES:
        requete += " AND cross = ?"
        parametres.append(filtres.cross)
    if filtres.famille != VALEUR_TOUTES:
        requete += " AND famille = ?"
        parametres.append(filtres.famille)
    if (filtres.mois_debut, filtres.mois_fin) != (MOIS_DEBUT_DEFAUT, MOIS_FIN_DEFAUT):
        requete += " AND mois BETWEEN ? AND ?"
        parametres.extend([int(filtres.mois_debut), int(filtres.mois_fin)])
    if filtres.perimetre == PERIMETRE_METROPOLE:
        requete += " AND est_metropolitain = 1"
    elif filtres.perimetre == PERIMETRE_OUTRE_MER:
        requete += " AND est_metropolitain = 0"
    return requete, parametres


def typer_categories(donnees: pd.DataFrame) -> pd.DataFrame:
    """Transforme les colonnes de classes en catégories ordonnées."""
    for colonne, ordre in ORDRES_CATEGORIES.items():
        if colonne in donnees:
            donnees[colonne] = pd.Categorical(
                donnees[colonne], categories=ordre, ordered=True
            )
    return donnees


@lru_cache(maxsize=16)
def charger_operations(filtres: Filtres) -> pd.DataFrame:
    """Charge les opérations correspondant aux filtres (résultat en cache).

    Le DataFrame retourné est partagé entre les graphiques : il ne doit pas
    être modifié en place (travailler sur une copie si nécessaire).
    """
    requete, parametres = construire_requete(filtres)
    with ouvrir_connexion() as connexion:
        donnees = pd.read_sql_query(requete, connexion, params=parametres)
    return typer_categories(donnees)


def calculer_kpi(donnees: pd.DataFrame) -> dict[str, float | None]:
    """Calcule les indicateurs clés affichés en tête de page."""
    duree_mediane = donnees["duree_heures"].median()
    return {
        "operations": float(len(donnees)),
        "secourues": float(donnees["personnes_secourues"].sum()),
        "blessees": float(donnees["personnes_blessees"].sum()),
        "decedees": float(donnees["personnes_decedees"].sum()),
        "duree_mediane": None if pd.isna(duree_mediane) else float(duree_mediane),
    }
