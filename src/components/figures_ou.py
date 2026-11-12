"""Figures de l'onglet « Où ? » : profils de risque des territoires."""

import pandas as pd
import plotly.graph_objects as go

from config import GRAVITES
from src.components.graphiques import (
    TextesFigure,
    barres_groupees,
    carte_chaleur,
    formater_effectif,
)
from src.components.theme import COULEURS_GRAVITE
from src.utils.aggregations import principales_modalites, profil_croise

# Nombre maximal de départements affichés (les plus actifs).
NOMBRE_DEPARTEMENTS = 15


def _profil_territoire(
    donnees: pd.DataFrame,
    territoire: str,
    titre: str,
    libelle: str,
    retenus: list[str] | None = None,
) -> go.Figure:
    """Répartition des familles d'événements dans chaque territoire (lignes à 100 %)."""
    if retenus is not None:
        donnees = donnees[donnees[territoire].isin(retenus)]
    tableau = profil_croise(donnees, territoire, "famille")
    pourcentages = tableau.pourcentages.T
    effectifs = tableau.effectifs.T
    if not pourcentages.empty:
        ordre = tableau.totaux[pourcentages.index].sort_values(ascending=False).index
        pourcentages, effectifs = pourcentages.loc[ordre], effectifs.loc[ordre]
    textes = TextesFigure(
        titre,
        "Chaque ligne = 100 % des opérations du territoire, classé du plus au moins actif · "
        f"{formater_effectif(int(tableau.totaux.sum()))} opérations",
        "Famille d'événements",
        libelle,
    )
    figure = carte_chaleur(pourcentages, effectifs, textes)
    figure.update_layout(height=max(380, 34 * len(pourcentages) + 160))
    return figure


def figure_cross_famille(donnees: pd.DataFrame) -> go.Figure:
    """CROSS × famille d'événements."""
    return _profil_territoire(donnees, "cross", "Profil des événements par CROSS", "CROSS")


def figure_departement_famille(donnees: pd.DataFrame) -> go.Figure:
    """Département × famille d'événements (les 15 départements les plus actifs)."""
    retenus = principales_modalites(donnees, "departement", NOMBRE_DEPARTEMENTS)
    return _profil_territoire(
        donnees, "departement",
        f"Profil des événements par département ({NOMBRE_DEPARTEMENTS} plus actifs)",
        "Département", retenus,
    )


def figure_zone_gravite(donnees: pd.DataFrame) -> go.Figure:
    """Part des opérations avec blessés, ou avec décès ou disparus, par façade."""
    tableau = profil_croise(donnees, "zone", "gravite")
    graves = tableau.pourcentages.drop(index=GRAVITES[0], errors="ignore")
    textes = TextesFigure(
        "Gravité des opérations selon la façade maritime",
        "Part des opérations de la façade ayant fait des blessés, ou des décès ou disparus",
        "Façade maritime",
        "% des opérations",
    )
    return barres_groupees(graves, textes, COULEURS_GRAVITE)
