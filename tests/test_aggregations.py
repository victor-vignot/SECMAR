"""Tests des agrégations statistiques (`src/utils/aggregations.py`)."""

import pandas as pd
import pytest

from src.utils.aggregations import (
    CLASSES_DISTANCE,
    classer_distance,
    comptage_par,
    evolution_annuelle,
    indicateurs_par_groupe,
    principales_modalites,
    profil_croise,
    quartiles_par_groupe,
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


def test_quartiles(operations: pd.DataFrame) -> None:
    """Médiane correcte ; groupe sous l'effectif minimal retiré."""
    resume = quartiles_par_groupe(operations, "vent", "duree", effectif_min=30)
    assert resume["vent"].tolist() == ["faible"]
    assert resume.loc[0, "mediane"] == pytest.approx(20.5)


def test_comptage_et_modalites(operations: pd.DataFrame) -> None:
    """Comptage par combinaison et valeurs les plus fréquentes."""
    comptage = comptage_par(operations, ["vent", "famille"])
    assert comptage["operations"].sum() == 50
    assert principales_modalites(operations, "famille", 1) == ["Avarie"]


def test_classes_de_distance() -> None:
    """0 mille = trait de côte ; 2 milles = 0,5 à 3 ; 40 milles = au-delà de 12."""
    classes = classer_distance(pd.Series([0.0, 2.0, 40.0]))
    assert classes.tolist() == [CLASSES_DISTANCE[0], CLASSES_DISTANCE[2], CLASSES_DISTANCE[4]]


def test_evolution_annuelle() -> None:
    """Opérations et décès ou disparus pour 1 000 opérations, par année et famille."""
    donnees = pd.DataFrame({
        "operation_id": [1, 2, 3, 4], "annee": [2020, 2020, 2020, 2021],
        "famille": ["Médical"] * 4, "personnes_decedees": [1, 0, 0, 0],
        "personnes_disparues": [0, 0, 0, 0], "personnes_impliquees_sans_clandestins": [2, 1, 1, 3],
    })
    ligne = evolution_annuelle(donnees).set_index("annee").loc[2020]
    assert ligne["operations"] == 3
    assert ligne["impliques"] == 4
    assert ligne["taux_victimes"] == pytest.approx(1000 / 3)
