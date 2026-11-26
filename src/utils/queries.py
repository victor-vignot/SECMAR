"""Requêtes SQLite utilisées par le tableau de bord, écrites avec SQLAlchemy.

Une seule requête filtrée lit la table `cleaned` ; son résultat est mis en
cache pour que tous les graphiques d'un même filtrage le réutilisent sans
relire la base. Les requêtes sont construites avec le langage d'expressions
de SQLAlchemy : les valeurs des filtres sont toujours des paramètres liés.
"""

import threading
from functools import lru_cache

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import Select, column, select, table

from config import (
    ANNEE_DEBUT_DEFAUT,
    ANNEE_FIN_DEFAUT,
    ANNEE_MAX,
    ANNEE_MIN,
    CLASSES_MER,
    CLASSES_VENT,
    GRAVITES,
    MOIS_DEBUT_DEFAUT,
    MOIS_FIN_DEFAUT,
    SAISONS,
    TABLE_CLEANED,
    VALEUR_TOUTES,
)
from src.utils.database import creer_moteur
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

# Description de la table `cleaned` pour SQLAlchemy (seules les colonnes utiles).
OPERATIONS = table(TABLE_CLEANED, *(column(nom) for nom in COLONNES_DASHBOARD))

# Ordre logique des catégories, utilisé par les graphiques.
ORDRES_CATEGORIES: dict[str, list[str]] = {
    "famille": ORDRE_FAMILLES,
    "classe_vent": list(CLASSES_VENT),
    "classe_mer": list(CLASSES_MER),
    "saison": list(SAISONS),
    "gravite": GRAVITES,
}


# Valeurs possibles du filtre de périmètre (expression vérifiée par pydantic).
MOTIF_PERIMETRE = f"^({PERIMETRE_TOUT}|{PERIMETRE_METROPOLE}|{PERIMETRE_OUTRE_MER})$"


class Filtres(BaseModel):
    """Valeurs sélectionnées dans le panneau de filtres, validées par pydantic.

    Le modèle est figé (`frozen`) : il est hachable, donc utilisable comme clé
    du cache de `charger_operations`. Une valeur hors bornes ou une période à
    l'envers lève une `ValidationError` avant d'atteindre la base.
    """

    model_config = ConfigDict(frozen=True)

    annee_debut: int = Field(default=ANNEE_DEBUT_DEFAUT, ge=ANNEE_MIN, le=ANNEE_MAX)
    annee_fin: int = Field(default=ANNEE_FIN_DEFAUT, ge=ANNEE_MIN, le=ANNEE_MAX)
    cross: str = VALEUR_TOUTES
    famille: str = VALEUR_TOUTES
    perimetre: str = Field(default=PERIMETRE_TOUT, pattern=MOTIF_PERIMETRE)
    mois_debut: int = Field(default=MOIS_DEBUT_DEFAUT, ge=1, le=12)
    mois_fin: int = Field(default=MOIS_FIN_DEFAUT, ge=1, le=12)

    @model_validator(mode="after")
    def verifier_ordre(self) -> Filtres:
        """Début avant fin, pour les années comme pour les mois."""
        if self.annee_debut > self.annee_fin or self.mois_debut > self.mois_fin:
            raise ValueError("le début doit précéder la fin")
        return self


def charger_options_filtres() -> tuple[list[str], list[str]]:
    """Retourne les CROSS et les familles disponibles dans la base."""
    colonnes = OPERATIONS.c
    with creer_moteur().connect() as connexion:
        cross = list(connexion.scalars(
            select(colonnes.cross)
            .distinct()
            .where(colonnes.cross.is_not(None))
            .order_by(colonnes.cross)
        ))
        familles_presentes = set(connexion.scalars(select(colonnes.famille).distinct()))
    familles = [f for f in ORDRE_FAMILLES if f in familles_presentes]
    return cross, familles


def construire_requete(filtres: Filtres) -> Select:
    """Construit la requête SQLAlchemy correspondant aux filtres."""
    colonnes = OPERATIONS.c
    requete = select(OPERATIONS).where(
        colonnes.annee.between(int(filtres.annee_debut), int(filtres.annee_fin))
    )
    if filtres.cross != VALEUR_TOUTES:
        requete = requete.where(colonnes.cross == filtres.cross)
    if filtres.famille != VALEUR_TOUTES:
        requete = requete.where(colonnes.famille == filtres.famille)
    if (filtres.mois_debut, filtres.mois_fin) != (MOIS_DEBUT_DEFAUT, MOIS_FIN_DEFAUT):
        requete = requete.where(
            colonnes.mois.between(int(filtres.mois_debut), int(filtres.mois_fin))
        )
    if filtres.perimetre == PERIMETRE_METROPOLE:
        requete = requete.where(colonnes.est_metropolitain == 1)
    elif filtres.perimetre == PERIMETRE_OUTRE_MER:
        requete = requete.where(colonnes.est_metropolitain == 0)
    return requete


def typer_categories(donnees: pd.DataFrame) -> pd.DataFrame:
    """Transforme les colonnes de classes en catégories ordonnées."""
    for colonne, ordre in ORDRES_CATEGORIES.items():
        if colonne in donnees:
            donnees[colonne] = pd.Categorical(
                donnees[colonne], categories=ordre, ordered=True
            )
    return donnees


_VERROU_CHARGEMENT = threading.Lock()


def charger_operations(filtres: Filtres) -> pd.DataFrame:
    """Charge les opérations correspondant aux filtres (résultat en cache).

    Le verrou garantit qu'une même requête n'est exécutée qu'une fois lorsque
    plusieurs callbacks la demandent simultanément : les suivants attendent
    puis lisent le cache. Le DataFrame retourné est partagé entre les
    graphiques : il ne doit pas être modifié en place.
    """
    with _VERROU_CHARGEMENT:
        return _lire_operations(filtres)


@lru_cache(maxsize=16)
def _lire_operations(filtres: Filtres) -> pd.DataFrame:
    """Exécute la requête filtrée et type les colonnes de classes."""
    with creer_moteur().connect() as connexion:
        donnees = pd.read_sql_query(construire_requete(filtres), connexion)
    return typer_categories(donnees)


def calculer_kpi(donnees: pd.DataFrame) -> dict[str, float | None]:
    """Calcule les indicateurs clés affichés en tête de page."""
    duree_mediane = donnees["duree_heures"].median()
    return {
        "operations": float(len(donnees)),
        "secourues": float(donnees["personnes_secourues"].sum()),
        "blessees": float(donnees["personnes_blessees"].sum()),
        # Décès et disparitions ensemble, comme dans toutes les analyses.
        "decedees": float(
            donnees["personnes_decedees"].sum() + donnees["personnes_disparues"].sum()
        ),
        "duree_mediane": None if pd.isna(duree_mediane) else float(duree_mediane),
    }
