"""Tests des messages « à retenir » (calculs et affichage)."""

import pandas as pd
import pytest

from src.components.messages import creer_bandeau_messages
from src.utils.messages import (
    Message,
    formater,
    message_medical_mer,
    messages_conditions,
    messages_consequences,
    messages_duree,
    messages_evolution,
    messages_ou,
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


def test_messages_ou(echantillon: pd.DataFrame) -> None:
    """CROSS le plus sollicité en premier ; aucun message pour un seul CROSS."""
    messages = messages_ou(echantillon)
    assert messages[0].titre.startswith(echantillon["cross"].value_counts().index[0])
    un_seul = echantillon[echantillon["cross"] == "Étel"]
    assert not messages_ou(un_seul)


def test_messages_evolution() -> None:
    """Hausse, année record et prudence quand la période traverse les ruptures."""
    donnees = pd.DataFrame({"annee": [2005] * 100 + [2015] * 400 + [2024] * 300})
    messages = messages_evolution(donnees)
    assert messages[0].titre == "Activité en hausse de 2005 à 2024"
    assert messages[1].titre == "2015 : l'année record"
    assert messages[2].titre == "Prudence sur 2009-2010 et 2019-2021"


def test_messages_evolution_sans_rupture() -> None:
    """Pas de message de prudence sur une période sans rupture de saisie."""
    donnees = pd.DataFrame({"annee": [2011] * 100 + [2017] * 120})
    assert len(messages_evolution(donnees)) == 2


def test_message_medical_mer() -> None:
    """Part médicale par mer très forte comparée à la mer calme, et part des îles."""
    calme = pd.DataFrame({"famille": ["Médical"] * 10 + ["Avarie ou panne"] * 90,
                          "evenement": ["Problème médical"] * 100})
    forte = pd.DataFrame({
        "famille": ["Médical"] * 40 + ["Avarie ou panne"] * 60,
        "evenement": ["Transport sanitaire île-continent"] * 10 + ["Problème médical"] * 90,
    })
    message = message_medical_mer(calme, forte)
    assert message is not None
    assert message.titre == "Mer forte : part médicale × 4,0"
    assert "40 % des opérations sont médicales, contre 10 %" in message.texte
    assert message_medical_mer(forte, calme) is None


def test_messages_quand_sur_quelques_mois(echantillon: pd.DataFrame) -> None:
    """Sur juin-août : référence sur 3 mois, pas de comparaison avec l'hiver."""
    ete = echantillon[echantillon["mois"].between(6, 8)]
    messages = messages_quand(ete)
    assert len(messages) == 1
    assert "sur les 3 mois choisis" in messages[0].texte
