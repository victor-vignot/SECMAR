"""Figures de l'onglet « Où ? » : profils de risque des territoires."""

import pandas as pd
import plotly.graph_objects as go

from src.components.graphiques import TextesFigure, carte_chaleur, formater_effectif
from src.utils.aggregations import profil_croise


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
    figure.update_xaxes(tickangle=-30)
    return figure


def figure_cross_famille(donnees: pd.DataFrame) -> go.Figure:
    """CROSS × famille d'événements."""
    return _profil_territoire(donnees, "cross", "Profil des événements par CROSS", "CROSS")
