"""Figures de l'onglet « Quand ? » : saisonnalité des opérations."""

import pandas as pd
import plotly.graph_objects as go

from config import NOMS_MOIS
from src.components.graphiques import TextesFigure, courbes
from src.components.theme import COULEURS_FAMILLES
from src.utils.aggregations import comptage_par


def figure_mois_famille(donnees: pd.DataFrame) -> go.Figure:
    """Nombre moyen d'opérations par mois et par an, une courbe par famille."""
    comptage = comptage_par(donnees, ["famille", "mois"])
    annees = donnees["annee"].nunique()
    if annees:
        # Moyenne annuelle : comparable quelle que soit la période choisie.
        comptage["operations"] = comptage["operations"] / annees
    textes = TextesFigure(
        "Les opérations au fil des mois, par famille d'événements",
        f"Nombre moyen d'opérations par mois et par an ({annees} années sélectionnées)",
        "Mois",
        "Opérations par an (moyenne)",
    )
    return courbes(
        comptage, ("mois", "operations", "famille"), COULEURS_FAMILLES, textes, NOMS_MOIS
    )
