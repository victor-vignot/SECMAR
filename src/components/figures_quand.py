"""Figures de l'onglet « Quand ? » : saisonnalité des opérations."""

import pandas as pd
import plotly.graph_objects as go

from config import NOMS_MOIS
from src.components.graphiques import TextesFigure, carte_chaleur, courbes
from src.components.theme import COULEURS_FAMILLES
from src.utils.aggregations import comptage_par, profil_croise


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


def figure_saison_famille(donnees: pd.DataFrame) -> go.Figure:
    """Répartition des familles d'événements à chaque saison (en %)."""
    tableau = profil_croise(donnees, "saison", "famille")
    textes = TextesFigure(
        "Quels événements à chaque saison ?",
        "Chaque colonne = 100 % des opérations de la saison (saisons de l'hémisphère nord)",
        "Saison",
        "Famille d'événements",
    )
    return carte_chaleur(tableau.pourcentages, tableau.effectifs, textes)


def figure_saison_zone(donnees: pd.DataFrame) -> go.Figure:
    """Part de chaque saison dans l'activité de chaque façade maritime (en %)."""
    tableau = profil_croise(donnees, "zone", "saison")
    textes = TextesFigure(
        "Quand les opérations ont-elles lieu, selon la façade ?",
        "Chaque colonne = 100 % des opérations de la façade · "
        "saisons de l'hémisphère nord, à nuancer en outre-mer",
        "Façade maritime",
        "Saison",
    )
    return carte_chaleur(tableau.pourcentages, tableau.effectifs, textes)
