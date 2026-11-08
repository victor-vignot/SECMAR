"""Tests des figures de l'onglet « Quand ? »."""

import pandas as pd

from src.components import figures_quand


def test_moyenne_annuelle_par_mois() -> None:
    """Deux années, deux opérations en juillet : une par an en moyenne."""
    donnees = pd.DataFrame(
        {"famille": ["Médical", "Médical"], "mois": [7, 7], "annee": [2020, 2021]}
    )
    figure = figures_quand.figure_mois_famille(donnees)
    assert list(figure.data[0].y) == [1.0]
