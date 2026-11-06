"""Figures de l'onglet « Conséquences » : bilan humain selon le type d'événement."""

import pandas as pd
import plotly.graph_objects as go

from src.components.graphiques import TextesFigure, barres_horizontales, figure_vide
from src.components.theme import COULEURS_FAMILLES
from src.utils.aggregations import indicateurs_par_groupe


def _indicateur_famille(
    donnees: pd.DataFrame,
    colonnes: list[str],
    pour: int,
    textes: TextesFigure,
    format_valeur: str,
) -> go.Figure:
    """Barres d'un indicateur humain (somme de `colonnes`) pour `pour` opérations."""
    if donnees.empty:
        return figure_vide(textes.titre)
    travail = donnees.assign(_indicateur=donnees[colonnes].sum(axis=1))
    resume = indicateurs_par_groupe(travail, "famille", ["_indicateur"], pour=pour)
    return barres_horizontales(
        resume, ("famille", "taux__indicateur"), textes, format_valeur, COULEURS_FAMILLES
    )


def figure_famille_deces(donnees: pd.DataFrame) -> go.Figure:
    """Décès et disparus pour 1 000 opérations, selon la famille."""
    return _indicateur_famille(
        donnees, ["personnes_decedees", "personnes_disparues"], 1000,
        TextesFigure(
            "Quelles familles d'événements sont les plus meurtrières ?",
            "Nombre de personnes décédées ou disparues pour 1 000 opérations",
            "Décès et disparus pour 1 000 opérations",
        ),
        ".0f",
    )


def figure_famille_blesses(donnees: pd.DataFrame) -> go.Figure:
    """Blessés pour 100 opérations, selon la famille."""
    return _indicateur_famille(
        donnees, ["personnes_blessees"], 100,
        TextesFigure(
            "Quelles familles d'événements font le plus de blessés ?",
            "Nombre de personnes blessées pour 100 opérations",
            "Blessés pour 100 opérations",
        ),
        ".1f",
    )
