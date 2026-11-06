"""Figures de l'onglet « Conditions » : vent et état de la mer."""

import pandas as pd
import plotly.graph_objects as go

from src.components.graphiques import TextesFigure, carte_chaleur, formater_effectif
from src.utils.aggregations import profil_croise

LIBELLES = {
    "classe_vent": "Force du vent (échelle de Beaufort)",
    "classe_mer": "État de la mer (échelle de Douglas)",
    "famille": "Famille d'événements",
}


def _profil_meteo_famille(donnees: pd.DataFrame, condition: str, titre: str) -> go.Figure:
    """Répartition des familles d'événements pour chaque classe météo."""
    tableau = profil_croise(donnees, condition, "famille")
    renseignees = int(tableau.totaux.sum())
    sous_titre = (
        f"Chaque colonne = 100 % des opérations de la classe · "
        f"{formater_effectif(renseignees)} opérations renseignées sur "
        f"{formater_effectif(len(donnees))}"
    )
    textes = TextesFigure(titre, sous_titre, LIBELLES[condition], LIBELLES["famille"])
    return carte_chaleur(tableau.pourcentages, tableau.effectifs, textes)


def figure_vent_famille(donnees: pd.DataFrame) -> go.Figure:
    """Force du vent × famille d'événements."""
    return _profil_meteo_famille(
        donnees, "classe_vent", "Quels événements selon la force du vent ?"
    )


def figure_mer_famille(donnees: pd.DataFrame) -> go.Figure:
    """État de la mer × famille d'événements."""
    return _profil_meteo_famille(
        donnees, "classe_mer", "Quels événements selon l'état de la mer ?"
    )
