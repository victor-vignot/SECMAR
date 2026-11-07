"""Figures de l'onglet « Durée et distance »."""

import pandas as pd
import plotly.graph_objects as go

from src.components.graphiques import TextesFigure, boites_quartiles
from src.utils.aggregations import quartiles_par_groupe

LIBELLES = {
    "classe_vent": "Force du vent (échelle de Beaufort)",
    "classe_mer": "État de la mer (échelle de Douglas)",
    "famille": "Famille d'événements",
}

SOUS_TITRE_BOITES = (
    "Boîte : 1er-3e quartile · trait : médiane · moustaches : 10e-90e centile · "
    "durées de 0 à 72 h"
)


def _duree_selon(donnees: pd.DataFrame, groupe: str, titre: str, horizontal: bool) -> go.Figure:
    """Distribution des durées d'opération par groupe."""
    resume = quartiles_par_groupe(donnees, groupe, "duree_heures")
    textes = TextesFigure(titre, SOUS_TITRE_BOITES, LIBELLES[groupe], "Durée (heures)")
    return boites_quartiles(resume, groupe, textes, horizontal)


def figure_duree_vent(donnees: pd.DataFrame) -> go.Figure:
    """Force du vent × durée des opérations."""
    return _duree_selon(
        donnees, "classe_vent", "Durée des opérations selon la force du vent", False
    )


def figure_duree_mer(donnees: pd.DataFrame) -> go.Figure:
    """État de la mer × durée des opérations."""
    return _duree_selon(
        donnees, "classe_mer", "Durée des opérations selon l'état de la mer", False
    )


def figure_duree_famille(donnees: pd.DataFrame) -> go.Figure:
    """Famille d'événements × durée des opérations."""
    return _duree_selon(
        donnees, "famille", "Durée des opérations selon la famille d'événements", True
    )
