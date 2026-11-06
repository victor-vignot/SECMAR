"""Tests de la page : registre des onglets, construction du contenu, callbacks."""

import pandas as pd
import pytest
from dash import html

from src.pages.dashboard import construire_onglet
from src.pages.onglets import ONGLETS, ONGLETS_PAR_IDENTIFIANT, Onglet
from src.utils.database import base_est_prete


def test_six_onglets_aux_identifiants_uniques() -> None:
    """Six onglets, chacun avec un identifiant unique et une question."""
    assert len(ONGLETS) == 6
    assert len(ONGLETS_PAR_IDENTIFIANT) == len(ONGLETS)
    assert all(onglet.question.endswith("?") for onglet in ONGLETS)


@pytest.mark.parametrize("onglet", ONGLETS, ids=lambda o: o.identifiant)
def test_construction_de_chaque_onglet(onglet: Onglet, echantillon: pd.DataFrame) -> None:
    """Chaque onglet se construit sans erreur et commence par sa question."""
    contenu = construire_onglet(onglet, echantillon)
    assert isinstance(contenu[0], html.P)
    assert contenu[0].children == onglet.question


@pytest.mark.skipif(not base_est_prete(), reason="base non construite")
def test_application_complete() -> None:
    """L'application se crée et ses deux callbacks répondent aux filtres."""
    from main import creer_application  # pylint: disable=import-outside-toplevel

    app = creer_application()
    callbacks = [c["callback"].__wrapped__ for c in app.callback_map.values()]
    assert len(callbacks) == 2
    filtres = ([2015, 2020], "toutes", "toutes", "metropole")
    assert callbacks[0](*filtres)[0] != "N/D"
    for onglet in ONGLETS:
        assert callbacks[1](onglet.identifiant, *filtres)
