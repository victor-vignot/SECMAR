"""Tests des messages « à retenir » (calculs et affichage)."""

import pandas as pd
import pytest

from src.components.messages import creer_bandeau_messages
from src.utils.messages import (
    Message,
    formater,
    messages_quand,
    part_en_pourcent,
    taux_pour_mille,
    victimes_graves,
)


def test_ton_inconnu_refuse() -> None:
    """Un message ne peut avoir qu'un des trois tons prévus."""
    with pytest.raises(ValueError):
        Message("Titre", "Texte", ton="rouge")


def test_formater_a_la_francaise() -> None:
    """Espace pour les milliers, virgule pour les décimales."""
    assert formater(12345.678, 1) == "12 345,7"


def test_taux_et_parts() -> None:
    """Taux pour 1 000 et part en % d'une condition."""
    masque = pd.Series([True, False, False, False])
    assert taux_pour_mille(masque) == pytest.approx(250)
    assert part_en_pourcent(masque) == pytest.approx(25)
    assert taux_pour_mille(pd.Series([], dtype=bool)) == 0


def test_victimes_graves() -> None:
    """Décès ou disparus comptent comme victimes graves, pas les blessés."""
    donnees = pd.DataFrame({"personnes_decedees": [0, 1, 0], "personnes_disparues": [0, 0, 2]})
    assert victimes_graves(donnees).tolist() == [False, True, True]


def test_bandeau_une_carte_par_message() -> None:
    """Une carte par message, avec la classe de son ton ; rien sans message."""
    bandeau = creer_bandeau_messages([Message("A", "a"), Message("B", "b", "grave")])
    assert bandeau is not None
    assert [carte.className for carte in bandeau.children] == [
        "message message--info", "message message--grave",
    ]
    assert creer_bandeau_messages([]) is None


def test_messages_quand(echantillon: pd.DataFrame) -> None:
    """Trois messages sur un échantillon complet, aucun sur une sélection trop petite."""
    messages = messages_quand(echantillon)
    assert len(messages) == 3
    assert "mois le plus chargé" in messages[0].titre
    assert not messages_quand(echantillon.head(10))
