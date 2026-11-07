"""Figures de l'onglet « Évolution » : les opérations de 1985 à aujourd'hui."""

import pandas as pd
import plotly.graph_objects as go

from config import RUPTURES_SAISIE
from src.components.graphiques import TextesFigure, courbes, figure_vide
from src.components.theme import COULEUR_SECONDAIRE, COULEURS_FAMILLES
from src.utils.aggregations import evolution_annuelle

MESSAGE_DEUX_ANNEES = "Choisissez au moins deux années pour voir une évolution"


def figure_courbe_annuelle(donnees: pd.DataFrame) -> go.Figure:
    """Nombre d'opérations par an, une courbe par famille, ruptures de saisie grisées."""
    titre = "Les opérations année après année, par famille d'événements"
    if donnees["annee"].nunique() < 2:
        return figure_vide(titre, MESSAGE_DEUX_ANNEES)
    evolution = evolution_annuelle(donnees)
    periodes = ", ".join(f"{debut}-{fin}" for debut, fin, _ in RUPTURES_SAISIE)
    textes = TextesFigure(
        titre,
        f"Nombre d'opérations par an · zones grisées ({periodes}) : changements dans "
        "la façon d'enregistrer les opérations, à prendre en compte dans les comparaisons",
        "Année",
        "Nombre d'opérations",
    )
    figure = courbes(evolution, ("annee", "operations", "famille"), COULEURS_FAMILLES, textes)
    annees = evolution["annee"]
    for debut, fin, _ in RUPTURES_SAISIE:
        if annees.min() <= fin and annees.max() >= debut:
            figure.add_vrect(
                x0=debut - 0.5, x1=fin + 0.5,
                fillcolor=COULEUR_SECONDAIRE, opacity=0.12, line_width=0,
            )
    return figure
