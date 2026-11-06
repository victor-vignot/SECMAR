"""Tests des figures de l'onglet « Conséquences »."""

from collections.abc import Callable

import pandas as pd
import plotly.graph_objects as go
import pytest

from src.components import figures_consequences

type FabriqueFigure = Callable[[pd.DataFrame], go.Figure]

FIGURES = [
    figures_consequences.figure_famille_deces,
    figures_consequences.figure_famille_blesses,
    figures_consequences.figure_famille_impliques,
    figures_consequences.figure_evacuations,
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


def test_blesses_pour_cent_operations() -> None:
    """Deux blessés pour quatre opérations : 50 pour 100 opérations."""
    donnees = pd.DataFrame({"famille": ["Médical"] * 4, "personnes_blessees": [1, 1, 0, 0]})
    figure = figures_consequences.figure_famille_blesses(donnees)
    assert figure.data[0].x[0] == pytest.approx(50)
