"""Vérifie que l'échantillon de test ressemble aux vraies données du tableau de bord."""

import pandas as pd

from src.utils.queries import COLONNES_DASHBOARD


def test_echantillon_a_les_colonnes_du_dashboard(echantillon: pd.DataFrame) -> None:
    """L'échantillon fictif contient toutes les colonnes lues dans la base."""
    assert set(COLONNES_DASHBOARD) <= set(echantillon.columns)
    assert len(echantillon) == 2_000
