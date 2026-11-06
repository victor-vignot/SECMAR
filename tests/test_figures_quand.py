"""Tests des figures de l'onglet « Quand ? »."""

from collections.abc import Callable

import pandas as pd
import plotly.graph_objects as go
import pytest

from src.components import figures_quand

type FabriqueFigure = Callable[[pd.DataFrame], go.Figure]

FIGURES = [
    figures_quand.figure_mois_famille,
]


@pytest.mark.parametrize("fonction", FIGURES, ids=lambda f: f.__name__)
def test_figure_avec_titre_et_donnees(fonction: FabriqueFigure, echantillon: pd.DataFrame) -> None:
    """Chaque figure a un titre et au moins une série de données."""
    figure = fonction(echantillon)
    assert isinstance(figure, go.Figure)
    assert figure.layout.title.text
    assert len(figure.data) >= 1


@pytest.mark.parametrize("fonction", FIGURES, ids=lambda f: f.__name__)
def test_figure_sans_donnees(fonction: FabriqueFigure, echantillon: pd.DataFrame) -> None:
    """Une sélection vide donne une figure explicative, sans erreur."""
    assert fonction(echantillon.iloc[0:0]).layout.annotations


def test_moyenne_annuelle_par_mois() -> None:
    """Deux années, deux opérations en juillet : une par an en moyenne."""
    donnees = pd.DataFrame(
        {"famille": ["Médical", "Médical"], "mois": [7, 7], "annee": [2020, 2021]}
    )
    figure = figures_quand.figure_mois_famille(donnees)
    assert list(figure.data[0].y) == [1.0]
