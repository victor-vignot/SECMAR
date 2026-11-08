"""Tests des figures de l'onglet « Conséquences »."""

import pandas as pd
import pytest

from src.components import figures_consequences


def test_blesses_pour_cent_operations() -> None:
    """Deux blessés pour quatre opérations : 50 pour 100 opérations."""
    donnees = pd.DataFrame({"famille": ["Médical"] * 4, "personnes_blessees": [1, 1, 0, 0]})
    figure = figures_consequences.figure_famille_blesses(donnees)
    assert figure.data[0].x[0] == pytest.approx(50)
