"""Figures de l'onglet « Conséquences » : bilan humain selon le type d'événement."""

import pandas as pd
import plotly.graph_objects as go

from src.components.graphiques import TextesFigure, barres_horizontales, figure_vide
from src.components.theme import COULEURS_FAMILLES
from src.utils.aggregations import comptage_par, indicateurs_par_groupe
from src.utils.familles import EVENEMENTS_EVACUATION


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


def figure_famille_impliques(donnees: pd.DataFrame) -> go.Figure:
    """Personnes impliquées par opération, selon la famille."""
    return _indicateur_famille(
        donnees, ["personnes_impliquees_sans_clandestins"], 1,
        TextesFigure(
            "Combien de personnes impliquées par opération ?",
            "Moyenne par opération, hors personnes clandestines (évite les valeurs extrêmes)",
            "Personnes impliquées par opération",
        ),
        ".1f",
    )


def figure_evacuations(donnees: pd.DataFrame) -> go.Figure:
    """Évacuations sanitaires et médicales, par type d'événement."""
    titre = "Évacuations sanitaires (EvaSan) et médicales (EvaMed)"
    evacuations = donnees[donnees["evenement"].isin(EVENEMENTS_EVACUATION)]
    if evacuations.empty:
        return figure_vide(titre, "Aucune évacuation enregistrée sur cette sélection")
    resume = comptage_par(evacuations, ["evenement"])
    derniere_annee = int(evacuations["annee"].max())
    textes = TextesFigure(
        titre,
        f"Nombre d'opérations · saisi seulement dans l'ancien système SECMARweb, "
        f"quasi absent après 2020 (dernière année : {derniere_annee})",
        "Nombre d'opérations",
    )
    return barres_horizontales(resume, ("evenement", "operations"), textes, ",.0f")
