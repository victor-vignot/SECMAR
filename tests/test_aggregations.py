"""Tests des agrégations statistiques (`src/utils/aggregations.py`)."""

import pandas as pd
import pytest

from src.utils.aggregations import (
    profil_croise,
)


@pytest.fixture(name="operations")
def fixture_operations() -> pd.DataFrame:
    """Petit jeu d'opérations fictives : 40 par vent faible, 10 par vent fort."""
    return pd.DataFrame({
        "vent": ["faible"] * 40 + ["fort"] * 10,
        "famille": ["Avarie"] * 30 + ["Baignade"] * 10 + ["Avarie"] * 10,
        "duree": list(range(1, 41)) + [5.0] * 10,
        "blesses": [0] * 39 + [1] + [2] * 10,
    })


def test_profil_croise_somme_a_cent(operations: pd.DataFrame) -> None:
    """Chaque groupe somme à 100 % ; un groupe trop petit est masqué."""
    tableau = profil_croise(operations, "vent", "famille", effectif_min=30)
    assert list(tableau.pourcentages.columns) == ["faible"]
    assert tableau.pourcentages["faible"].sum() == pytest.approx(100)
    assert tableau.pourcentages.loc["Avarie", "faible"] == pytest.approx(75)
    assert tableau.totaux["fort"] == 10
