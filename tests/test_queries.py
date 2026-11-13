"""Tests de la couche de requêtes et de la base SQLite."""

import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from config import VALEUR_TOUTES
from src.utils.database import base_est_prete, creer_archive, restaurer_archive
from src.utils.queries import (
    PERIMETRE_METROPOLE,
    Filtres,
    calculer_kpi,
    charger_operations,
    charger_options_filtres,
    construire_requete,
)

BASE_PRETE = base_est_prete()


def test_requete_sans_filtre() -> None:
    """Sans filtre, seule la période est paramétrée."""
    requete, parametres = construire_requete(Filtres(2005, 2025))
    assert "annee BETWEEN ? AND ?" in requete
    assert parametres == [2005, 2025]


def test_requete_avec_tous_les_filtres() -> None:
    """Chaque filtre ajoute une condition paramétrée (pas d'injection SQL)."""
    filtres = Filtres(2010, 2020, "Étel", "Médical", PERIMETRE_METROPOLE)
    requete, parametres = construire_requete(filtres)
    assert "cross = ?" in requete and "famille = ?" in requete
    assert "est_metropolitain = 1" in requete
    assert parametres == [2010, 2020, "Étel", "Médical"]


def test_requete_avec_mois() -> None:
    """Le filtre des mois n'ajoute une condition que s'il restreint l'année."""
    requete, parametres = construire_requete(Filtres(2010, 2020, mois_debut=6, mois_fin=8))
    assert "mois BETWEEN ? AND ?" in requete
    assert parametres == [2010, 2020, 6, 8]
    assert "mois" not in construire_requete(Filtres(2010, 2020))[0].split("WHERE")[1]


def test_kpi_sur_petit_tableau() -> None:
    """Les KPI additionnent les comptages et prennent la durée médiane."""
    donnees = pd.DataFrame({
        "personnes_secourues": [1, 2],
        "personnes_blessees": [0, 1],
        "personnes_decedees": [0, 1],
        "personnes_disparues": [2, 0],
        "duree_heures": [1.0, 3.0],
    })
    kpi = calculer_kpi(donnees)
    assert kpi["operations"] == 2
    assert kpi["secourues"] == 3
    assert kpi["decedees"] == 3
    assert kpi["duree_mediane"] == pytest.approx(2.0)


def test_archive_aller_retour(tmp_path: Path) -> None:
    """L'archive garde raw et cleaned, retire les autres tables."""
    base = tmp_path / "db.sqlite"
    with sqlite3.connect(base) as connexion:
        for table in ("raw", "cleaned", "raw_operations"):
            connexion.execute(f"CREATE TABLE {table} (x INTEGER)")
            connexion.execute(f"INSERT INTO {table} VALUES (1)")
    connexion.close()
    archive = tmp_path / "db.sqlite.xz"
    creer_archive(base, archive)

    restauree = tmp_path / "restauree.sqlite"
    assert restaurer_archive(archive, restauree)
    with sqlite3.connect(restauree) as connexion:
        tables = {t[0] for t in connexion.execute("SELECT name FROM sqlite_master")}
    connexion.close()
    assert tables == {"raw", "cleaned"}


def test_restauration_ne_remplace_pas_une_base(tmp_path: Path) -> None:
    """Une base existante n'est jamais écrasée par l'archive."""
    base = tmp_path / "db.sqlite"
    base.write_bytes(b"existante")
    archive = tmp_path / "db.sqlite.xz"
    archive.write_bytes(b"")
    assert not restaurer_archive(archive, base)
    assert base.read_bytes() == b"existante"


@pytest.mark.skipif(not BASE_PRETE, reason="base non construite")
def test_resultats_identiques_a_l_ancien_dashboard() -> None:
    """Les KPI 2005-2025 sont ceux mesurés avant la refonte."""
    donnees = charger_operations(Filtres(2005, 2025))
    kpi = calculer_kpi(donnees)
    assert kpi["operations"] == 250_726
    assert kpi["secourues"] == 187_939


@pytest.mark.skipif(not BASE_PRETE, reason="base non construite")
def test_options_et_filtre_famille() -> None:
    """Les options viennent de la base et le filtre famille est respecté."""
    cross, familles = charger_options_filtres()
    assert "Étel" in cross and "Agde" in cross and "Adge" not in cross
    donnees = charger_operations(Filtres(2005, 2025, VALEUR_TOUTES, familles[0]))
    assert set(donnees["famille"].dropna()) == {familles[0]}
