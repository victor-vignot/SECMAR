"""Tests de l'inspection en lecture seule des CSV."""

from pathlib import Path

import pandas as pd

from src.utils.inspect_data import inspecter


def test_inspection_par_blocs(tmp_path: Path) -> None:
    """Lignes, valeurs manquantes, période et modalités sont bien comptées."""
    fichier = tmp_path / "operations.csv"
    fichier.write_text(
        "date,evenement,vent\n"
        "2020-01-05,Baignade,3\n"
        "2021-07-14,Baignade,\n"
        "2019-03-01,,5\n",
        encoding="utf-8",
    )
    inspection = inspecter(fichier)
    assert inspection.lignes == 3
    assert inspection.colonnes == ["date", "evenement", "vent"]
    assert inspection.manquants is not None
    assert inspection.manquants["vent"] == 1
    assert inspection.premiere_date == pd.Timestamp("2019-03-01")
    assert inspection.derniere_date == pd.Timestamp("2021-07-14")
    assert inspection.modalites["evenement"] == {"Baignade": 2, "[MANQUANT]": 1}
