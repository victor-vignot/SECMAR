"""Tests des fonctions de nettoyage (`src/utils/clean_data.py`)."""

import pandas as pd
import pytest
import shapely

from config import CLASSES_VENT, DB_PATH, GRAVITES, ZONE_INCONNUE, ZONE_OUTRE_MER
from src.utils.clean_data import (
    calculer_duree_heures,
    calculer_gravite,
    calculer_saison,
    calculer_zone,
    classer_force,
    convertir_booleen,
    filtrer_distance_fiable,
    nettoyer,
    positions_invalides,
)
from src.utils.database import base_est_prete, ouvrir_connexion


def test_duree_en_heures_et_valeurs_aberrantes() -> None:
    """Durée correcte ; nulle, négative ou trop longue -> manquante."""
    debut = pd.Series(["2024-07-01 10:00:00+00:00"] * 4)
    fin = pd.Series([
        "2024-07-01 11:30:00+00:00",  # 1,5 h
        "2024-07-01 10:00:00+00:00",  # 0 h
        "2024-07-01 09:00:00+00:00",  # négative
        "2024-07-10 10:00:00+00:00",  # 216 h > 72 h
    ])
    duree = calculer_duree_heures(debut, fin, duree_max=72)
    assert duree.iloc[0] == pytest.approx(1.5)
    assert duree.iloc[1:].isna().all()


def test_saison() -> None:
    """Décembre est en hiver, juillet en été."""
    assert calculer_saison(pd.Series([12, 7, 4, 10])).tolist() == [
        "Hiver", "Été", "Printemps", "Automne",
    ]


def test_gravite_ordre_de_priorite() -> None:
    """Décès ou disparus l'emporte sur blessés, qui l'emporte sur rien."""
    blesses = pd.Series([0, 2, 1, 0])
    decedes = pd.Series([0, 0, 1, 0])
    disparus = pd.Series([0, 0, 0, 3])
    assert calculer_gravite(blesses, decedes, disparus).tolist() == [
        GRAVITES[0], GRAVITES[1], GRAVITES[2], GRAVITES[2],
    ]


def test_classe_de_vent() -> None:
    """Chaque force tombe dans la bonne classe ; force absente -> manquant."""
    classes = classer_force(pd.Series([0, 4, 7, 11, None], dtype="Int64"), CLASSES_VENT)
    libelles = list(CLASSES_VENT)
    assert classes.iloc[:4].tolist() == [libelles[0], libelles[1], libelles[2], libelles[3]]
    assert pd.isna(classes.iloc[4])


def test_booleen() -> None:
    """« True »/« False » deviennent 1/0."""
    assert convertir_booleen(pd.Series(["True", "False"])).tolist() == [1, 0]


def test_zone() -> None:
    """Façade en métropole, « Outre-mer » sinon, « Non renseignée » si absente."""
    zone = calculer_zone(
        pd.Series(["manche", None, None]),
        pd.Series([1, 0, 1], dtype="Int64"),
    )
    assert zone.tolist() == ["Manche - mer du Nord", ZONE_OUTRE_MER, ZONE_INCONNUE]


def test_distance_fiable_seulement_en_metropole() -> None:
    """Distance gardée en métropole, retirée en outre-mer et si la position est fausse."""
    distance = filtrer_distance_fiable(
        pd.Series([1.2, 2523.0, 4891.0]),
        pd.Series([True, False, True]),
        pd.Series([1, 1, 0], dtype="Int64"),
    )
    assert distance.iloc[0] == pytest.approx(1.2)
    assert distance.iloc[1:].isna().all()


def test_positions_invalides_sans_trait_de_cote() -> None:
    """Sans trait de côte, seules les positions (0, 0) sont invalides."""
    invalides = positions_invalides(
        pd.Series([0.0, 47.0, None]), pd.Series([0.0, -3.0, None]), None
    )
    assert invalides.tolist() == [True, False, False]


def test_positions_a_terre_retirees() -> None:
    """Une position au milieu d'une « terre » fictive est retirée."""
    terre = shapely.box(0, 40, 10, 50)  # carré de 10° de côté
    invalides = positions_invalides(
        pd.Series([45.0, 45.0, 55.0]), pd.Series([5.0, 0.01, 5.0]), terre
    )
    # Centre du carré : à terre loin de la côte ; bord du carré : à moins de 5 km ;
    # hors du carré : en mer.
    assert invalides.tolist() == [True, False, False]


def test_nettoyer_sur_un_petit_echantillon() -> None:
    """Le nettoyage produit une ligne typée par opération."""
    raw = pd.DataFrame({
        "operation_id": ["1"], "cross": ["Adge"], "departement": ["Réunion"],
        "est_metropolitain": ["True"], "evenement": ["Baignade"],
        "categorie_evenement": ["Accidents individuels à personnes"],
        "zone_responsabilite": ["Plage et 300 mètres"],
        "latitude": ["43.3"], "longitude": ["3.5"], "vent_force": ["3"],
        "mer_force": ["2"], "date_heure_reception_alerte": ["2020-08-01 14:00:00+00:00"],
        "date_heure_fin_operation": ["2020-08-01 15:00:00+00:00"],
        "systeme_source": ["secmarweb"], "annee": ["2020"], "mois": ["8"],
        "prefecture_maritime": ["mediterranee"], "distance_cote_milles_nautiques": ["0.1"],
        "nombre_personnes_impliquees": ["2"],
        "nombre_personnes_impliquees_sans_clandestins": ["2"],
        "nombre_personnes_blessees": ["1"], "nombre_personnes_decedees": ["0"],
        "nombre_personnes_disparues": ["0"], "nombre_personnes_secourues": ["2"],
    }, dtype="string")
    ligne = nettoyer(raw).iloc[0]
    assert ligne["cross"] == "Agde"
    assert ligne["departement"] == "La Réunion"
    assert ligne["famille"] == "Baignade et loisirs"
    assert ligne["saison"] == "Été"
    assert ligne["zone"] == "Méditerranée"
    assert ligne["gravite"] == GRAVITES[1]
    assert ligne["duree_heures"] == pytest.approx(1.0)


@pytest.mark.skipif(not base_est_prete(), reason="base non construite")
def test_table_cleaned_complete() -> None:
    """La table `cleaned` contient toutes les opérations, sans doublon."""
    with ouvrir_connexion(DB_PATH) as connexion:
        total, distincts = connexion.execute(
            "SELECT COUNT(*), COUNT(DISTINCT operation_id) FROM cleaned"
        ).fetchone()
        brut = connexion.execute("SELECT COUNT(*) FROM raw").fetchone()[0]
    assert total == distincts == brut
    assert total >= 394_756


@pytest.mark.skipif(not base_est_prete(), reason="base non construite")
def test_aucune_position_fausse_dans_cleaned() -> None:
    """Plus aucune position (0, 0) ; les positions retirées restent comptées."""
    with ouvrir_connexion(DB_PATH) as connexion:
        nulles = connexion.execute(
            "SELECT COUNT(*) FROM cleaned WHERE latitude = 0 AND longitude = 0"
        ).fetchone()[0]
        sans_position = connexion.execute(
            "SELECT COUNT(*) FROM cleaned WHERE latitude IS NULL"
        ).fetchone()[0]
    assert nulles == 0
    # 54 941 positions absentes à l'origine + les positions retirées.
    assert sans_position > 54_941
