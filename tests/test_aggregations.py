"""Tests des agrégations statistiques (`src/utils/aggregations.py`)."""

import pandas as pd
import pytest

from src.utils.aggregations import (
    indicateurs_par_groupe,
    profil_croise,
    taux_par_cases,
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


def test_taux_par_cases(operations: pd.DataFrame) -> None:
    """Part des opérations avec blessés dans chaque case."""
    taux, effectifs = taux_par_cases(
        operations, "famille", "vent", operations["blesses"].gt(0), effectif_min=1
    )
    assert taux.loc["Avarie", "fort"] == pytest.approx(100)
    assert effectifs.loc["Avarie", "faible"] == 30


def test_indicateurs_par_groupe(operations: pd.DataFrame) -> None:
    """Totaux, moyennes et taux pour 100 opérations."""
    resultat = indicateurs_par_groupe(operations, "vent", ["blesses"], pour=100)
    fort = resultat.set_index("vent").loc["fort"]
    assert fort["operations"] == 10
    assert fort["total_blesses"] == 20
    assert fort["taux_blesses"] == pytest.approx(200)
