"""Tests des figures de l'onglet « Durée et distance »."""

from collections.abc import Callable

import pandas as pd
import plotly.graph_objects as go
import pytest

from src.components import figures_duree

type FabriqueFigure = Callable[[pd.DataFrame], go.Figure]

FIGURES = [
    figures_duree.figure_duree_vent,
    figures_duree.figure_duree_mer,
    figures_duree.figure_duree_famille,
    figures_duree.figure_distance_cote,
    figures_duree.figure_gravite_distance,
]


@pytest.mark.parametrize("fonction", FIGURES, ids=lambda f: f.__name__)
def test_figure_avec_titre_et_axes(fonction: FabriqueFigure, echantillon: pd.DataFrame) -> None:
    """Chaque figure a un titre, des données et des axes nommés."""
    figure = fonction(echantillon)
    assert isinstance(figure, go.Figure)
    assert figure.layout.title.text
    assert figure.layout.xaxis.title.text


@pytest.mark.parametrize("fonction", FIGURES, ids=lambda f: f.__name__)
def test_figure_sans_donnees(fonction: FabriqueFigure, echantillon: pd.DataFrame) -> None:
    """Une sélection vide donne une figure explicative, sans erreur."""
    assert fonction(echantillon.iloc[0:0]).layout.annotations


def test_histogramme_limite_a_la_plage_affichee(echantillon: pd.DataFrame) -> None:
    """L'histogramme exclut les distances nulles et au-delà de 30 milles."""
    valeurs = pd.Series(figures_duree.figure_distance_cote(echantillon).data[0].x)
    assert valeurs.gt(0).all()
    assert valeurs.le(30).all()


def test_gravite_distance_dans_l_ordre_des_classes() -> None:
    """Les classes restent dans l'ordre : trait de côte en haut, large en bas."""
    donnees = pd.DataFrame({
        "distance_cote_mn": [0.0, 0.2, 1.0, 5.0, 20.0],
        "personnes_decedees": [1, 0, 0, 0, 1],
        "personnes_disparues": [0, 0, 0, 0, 0],
    })
    barres = figures_duree.figure_gravite_distance(donnees).data[0]
    # Plotly trace de bas en haut : le trait de côte est le dernier élément.
    assert list(barres.y) == [
        "Au-delà de 12 milles", "3 à 12 milles", "0,5 à 3 milles",
        "Moins de 0,5 mille", "Au trait de côte",
    ]
