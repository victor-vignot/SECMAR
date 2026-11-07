"""Tests des figures de l'onglet « Où ? »."""

from collections.abc import Callable

import pandas as pd
import plotly.graph_objects as go
import pytest

from src.components import figures_ou

type FabriqueFigure = Callable[[pd.DataFrame], go.Figure]

FIGURES = [
    figures_ou.figure_cross_famille,
    figures_ou.figure_departement_famille,
    figures_ou.figure_zone_gravite,
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


def test_cross_classes_du_plus_actif(echantillon: pd.DataFrame) -> None:
    """Le CROSS le plus actif est sur la première ligne de la carte de chaleur."""
    figure = figures_ou.figure_cross_famille(echantillon)
    assert figure.data[0].y[0] == echantillon["cross"].value_counts().index[0]


def test_departements_limites_aux_plus_actifs(echantillon: pd.DataFrame) -> None:
    """Au plus 15 départements sont affichés."""
    figure = figures_ou.figure_departement_famille(echantillon)
    assert len(figure.data[0].y) <= figures_ou.NOMBRE_DEPARTEMENTS
