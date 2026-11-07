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
