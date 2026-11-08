"""Règles communes à tous les graphiques des six onglets."""

import pandas as pd
import plotly.graph_objects as go
import pytest

from src.pages.onglets import ONGLETS, FonctionFigure

FIGURES = [graphique.fonction for onglet in ONGLETS for graphique in onglet.graphiques]


def test_chaque_graphique_est_affiche_une_seule_fois() -> None:
    """Aucun graphique n'apparaît dans deux onglets."""
    assert len(FIGURES) == len(set(FIGURES))


@pytest.mark.parametrize("fonction", FIGURES, ids=lambda f: f.__name__)
def test_figure_avec_titre_axes_et_donnees(
    fonction: FonctionFigure, grand_echantillon: pd.DataFrame
) -> None:
    """Chaque figure a un titre, des axes nommés et au moins une série."""
    figure = fonction(grand_echantillon)
    assert isinstance(figure, go.Figure)
    assert figure.layout.title.text
    assert figure.layout.xaxis.title.text or figure.layout.yaxis.title.text
    assert len(figure.data) >= 1


@pytest.mark.parametrize("fonction", FIGURES, ids=lambda f: f.__name__)
def test_figure_sans_donnees(fonction: FonctionFigure, echantillon: pd.DataFrame) -> None:
    """Une sélection vide donne une figure explicative, sans erreur."""
    figure = fonction(echantillon.iloc[0:0])
    assert figure.layout.title.text
    assert figure.layout.annotations
