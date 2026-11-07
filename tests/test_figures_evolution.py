"""Tests des figures de l'onglet « Évolution »."""

from collections.abc import Callable

import pandas as pd
import plotly.graph_objects as go
import pytest

from src.components import figures_evolution

type FabriqueFigure = Callable[[pd.DataFrame], go.Figure]

FIGURES = [
    figures_evolution.figure_courbe_annuelle,
]


@pytest.fixture(name="grand_echantillon")
def fixture_grand_echantillon(echantillon: pd.DataFrame) -> pd.DataFrame:
    """L'échantillon répété 10 fois : assez d'opérations par famille et par an."""
    return pd.concat([echantillon] * 10, ignore_index=True)


@pytest.mark.parametrize("fonction", FIGURES, ids=lambda f: f.__name__)
def test_figure_avec_titre_et_donnees(
    fonction: FabriqueFigure, grand_echantillon: pd.DataFrame
) -> None:
    """Chaque figure a un titre et au moins une série de données."""
    figure = fonction(grand_echantillon)
    assert isinstance(figure, go.Figure)
    assert figure.layout.title.text
    assert len(figure.data) >= 1


@pytest.mark.parametrize("fonction", FIGURES, ids=lambda f: f.__name__)
def test_une_seule_annee(fonction: FabriqueFigure, echantillon: pd.DataFrame) -> None:
    """Avec une seule année, la figure invite à élargir la période."""
    une_annee = echantillon[echantillon["annee"] == 2015]
    assert fonction(une_annee).layout.annotations


def test_ruptures_grisees(echantillon: pd.DataFrame) -> None:
    """Les deux périodes de rupture (2009-2010, 2019-2021) sont grisées."""
    figure = figures_evolution.figure_courbe_annuelle(echantillon)
    assert [forme.x0 for forme in figure.layout.shapes] == [2008.5, 2018.5]
