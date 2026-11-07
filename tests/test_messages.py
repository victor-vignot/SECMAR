"""Tests des messages « à retenir » (calculs et affichage)."""

import pandas as pd
import pytest

from src.components.messages import creer_bandeau_messages
from src.utils.messages import (
    Message,
    formater,
    messages_conditions,
    messages_consequences,
    messages_duree,
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


def test_messages_conditions_mer_forte() -> None:
    """La mortalité par mer très forte est comparée à celle par mer calme."""
    donnees = pd.DataFrame({
        "classe_mer": ["0-2 calme"] * 200 + ["5+ très forte"] * 200,
        "classe_vent": ["0-3 faible"] * 400,
        "famille": ["Médical"] * 400,
        "personnes_decedees": [0] * 198 + [1] * 2 + [0] * 190 + [1] * 10,
        "personnes_disparues": [0] * 400,
    })
    messages = messages_conditions(donnees)
    assert messages[0].ton == "grave"
    assert "× 5,0" in messages[0].titre


def test_messages_consequences(echantillon: pd.DataFrame) -> None:
    """Famille la plus meurtrière, plus de blessés, part avec victimes."""
    messages = messages_consequences(echantillon)
    assert [m.ton for m in messages] == ["grave", "alerte", "info"]
    assert not messages_consequences(echantillon.head(10))


def test_messages_duree(echantillon: pd.DataFrame) -> None:
    """Message de proximité et classe de distance la plus grave sur l'échantillon."""
    titres = [m.titre for m in messages_duree(echantillon)]
    assert "Un secours de proximité" in titres
    assert any(titre.startswith("Mortalité la plus forte") for titre in titres)
