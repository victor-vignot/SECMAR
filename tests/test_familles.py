"""Tests du regroupement des événements en familles."""

import sqlite3

import pytest

from config import DB_PATH, TABLE_RAW
from src.utils.familles import (
    CORRESPONDANCE_FAMILLES,
    EVENEMENTS_EVACUATION,
    FAMILLE_INCONNUE,
    FAMILLES_EVENEMENTS,
    ORDRE_FAMILLES,
    famille_de,
)


def test_soixante_huit_evenements_classes() -> None:
    """Les 68 événements connus sont rangés dans une seule famille."""
    assert len(CORRESPONDANCE_FAMILLES) == 68


def test_famille_connue() -> None:
    """Un événement connu retourne sa famille."""
    assert famille_de("Baignade") == "Baignade et loisirs"
    assert famille_de("Toutes fausses alertes") == (
        "Fausse alerte ou situation indéterminée"
    )


def test_famille_inconnue() -> None:
    """Une valeur absente ou inconnue retourne « Non renseigné »."""
    assert famille_de(None) == FAMILLE_INCONNUE
    assert famille_de("Valeur inventée") == FAMILLE_INCONNUE


def test_evacuations_dans_famille_medicale() -> None:
    """Les évacuations sanitaires font partie de la famille « Médical »."""
    for evenement in EVENEMENTS_EVACUATION:
        assert famille_de(evenement) == "Médical"


def test_ordre_contient_toutes_les_familles() -> None:
    """L'ordre d'affichage reprend chaque famille une seule fois."""
    assert ORDRE_FAMILLES[:-1] == list(FAMILLES_EVENEMENTS)
    assert len(set(ORDRE_FAMILLES)) == len(ORDRE_FAMILLES)


def _evenements_de_la_base() -> list[str]:
    """Lit les événements distincts présents dans la table brute."""
    with sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True) as connexion:
        lignes = connexion.execute(
            f"SELECT DISTINCT evenement FROM {TABLE_RAW} "
            "WHERE evenement IS NOT NULL"
        ).fetchall()
    connexion.close()
    return [ligne[0] for ligne in lignes]


def test_tous_les_evenements_de_la_base_sont_classes() -> None:
    """Chaque événement réellement présent dans les données a une famille."""
    try:
        evenements = _evenements_de_la_base()
    except sqlite3.Error:
        pytest.skip("Table brute absente : lancer d'abord clean_data.py")
    non_classes = [e for e in evenements if e not in CORRESPONDANCE_FAMILLES]
    assert not non_classes, f"Événements sans famille : {non_classes}"
