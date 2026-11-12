"""Tests propres aux graphiques de l'onglet « Conditions »."""

import pandas as pd

from src.components import figures_conditions
from src.components.theme import COULEUR_ACCENT


def test_ligne_medicale_encadree(echantillon: pd.DataFrame) -> None:
    """La ligne « Médical » de l'état de la mer est encadrée."""
    figure = figures_conditions.figure_mer_famille(echantillon)
    assert [forme.line.color for forme in figure.layout.shapes] == [COULEUR_ACCENT]
