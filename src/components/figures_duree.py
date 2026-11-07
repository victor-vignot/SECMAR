"""Figures de l'onglet « Durée et distance »."""

import pandas as pd
import plotly.graph_objects as go

from config import DISTANCE_MAX_HISTOGRAMME_MN, LARGEUR_CLASSE_DISTANCE_MN
from src.components.graphiques import (
    TextesFigure,
    barres_horizontales,
    boites_quartiles,
    figure_vide,
    histogramme,
)
from src.utils.aggregations import (
    classer_distance,
    indicateurs_par_groupe,
    quartiles_par_groupe,
)

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


def figure_distance_cote(donnees: pd.DataFrame) -> go.Figure:
    """Histogramme de la distance entre l'opération et la côte (métropole)."""
    titre = "À quelle distance de la côte ont lieu les opérations ?"
    distances = donnees["distance_cote_mn"].dropna()
    if distances.empty:
        return figure_vide(titre, "Distance disponible uniquement pour la métropole")
    au_bord = distances.eq(0).mean() * 100
    au_large = distances.gt(DISTANCE_MAX_HISTOGRAMME_MN).mean() * 100
    affichees = distances[distances.gt(0) & distances.le(DISTANCE_MAX_HISTOGRAMME_MN)]
    textes = TextesFigure(
        titre,
        f"Métropole · {au_bord:.0f} % des opérations à 0 mille (plage, port) et "
        f"{au_large:.0f} % au-delà de {DISTANCE_MAX_HISTOGRAMME_MN:.0f} milles, "
        "non représentées",
        "Distance à la côte (milles nautiques)",
        "Nombre d'opérations (échelle log)",
    )
    figure = histogramme(
        affichees, textes, (0, DISTANCE_MAX_HISTOGRAMME_MN, LARGEUR_CLASSE_DISTANCE_MN)
    )
    # Échelle logarithmique : les opérations proches du bord écrasent sinon
    # toutes les autres classes.
    figure.update_yaxes(type="log", dtick=1)
    return figure


def figure_gravite_distance(donnees: pd.DataFrame) -> go.Figure:
    """Décès et disparus pour 1 000 opérations, selon la distance à la côte."""
    titre = "La mortalité selon la distance à la côte"
    metropole = donnees.dropna(subset=["distance_cote_mn"])
    if metropole.empty:
        return figure_vide(titre, "Distance disponible uniquement pour la métropole")
    travail = metropole.assign(
        classe_distance=classer_distance(metropole["distance_cote_mn"]),
        victimes=metropole["personnes_decedees"] + metropole["personnes_disparues"],
    )
    resume = indicateurs_par_groupe(travail, "classe_distance", ["victimes"], pour=1000)
    textes = TextesFigure(
        titre,
        "Métropole · personnes décédées ou disparues pour 1 000 opérations",
        "Décès et disparus pour 1 000 opérations",
    )
    # Ordre des classes conservé : de la côte vers le large, de haut en bas.
    return barres_horizontales(
        resume, ("classe_distance", "taux_victimes"), textes, ".0f", trier=False
    )
