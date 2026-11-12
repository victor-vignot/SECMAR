"""Tests de la carte des opérations."""

import pandas as pd

from src.components import carte
from src.utils.familles import FAMILLE_INCONNUE


def test_infobulle_detaillee() -> None:
    """Chaque opération a son texte : type, période, personnes, distance, durée."""
    points = pd.DataFrame({
        "evenement": ["Baignade"], "famille": ["Baignade et loisirs"], "cross": ["Étel"],
        "mois": [7], "annee": [2024], "personnes_impliquees": [3.0],
        "personnes_secourues": [2.0], "personnes_blessees": [1.0],
        "personnes_decedees": [0.0], "personnes_disparues": [1.0],
        "distance_cote_mn": [0.45], "duree_heures": [1.5],
    })
    details = carte.details_operations(points).iloc[0]
    assert details["periode"] == "Juillet 2024"
    assert details["decedees"] == "1"
    assert details["distance"] == "0,5 milles"
    assert details["duree"] == "1 h 30"


def test_cadrage_sur_la_selection(echantillon: pd.DataFrame) -> None:
    """La carte se centre sur les points et zoome raisonnablement."""
    centre, zoom = carte.cadrage(echantillon)
    assert 42 < centre["lat"] < 51
    assert -5 < centre["lon"] < 8
    assert 3 < zoom < carte.ZOOM_MAXIMAL


def test_cadrage_sans_point() -> None:
    """Sans point, la carte garde le cadrage par défaut."""
    vide = pd.DataFrame(columns=["latitude", "longitude", "est_metropolitain"])
    assert carte.cadrage(vide) == (carte.CENTRE_PAR_DEFAUT, carte.ZOOM_PAR_DEFAUT)


def test_points_sans_famille_non_dessines(echantillon: pd.DataFrame) -> None:
    """Les opérations « Non renseigné » ne sont pas dessinées."""
    donnees = echantillon.astype({"famille": str})
    donnees.loc[:9, "famille"] = FAMILLE_INCONNUE
    assert len(carte.positions_valides(donnees)) == len(donnees) - 10


def test_mode_type_precis(echantillon: pd.DataFrame) -> None:
    """Mode « type précis » : au plus 8 types, les autres regroupés."""
    donnees = echantillon.assign(evenement=[f"Type {i % 12}" for i in range(len(echantillon))])
    figure = carte.creer_carte(donnees, carte.MODE_EVENEMENT)
    noms = [trace.name for trace in figure.data]
    assert len(noms) == carte.NOMBRE_TYPES_CARTE + 1
    assert noms[-1].startswith(carte.AUTRES_TYPES)


def test_legende_avec_effectifs_reels(echantillon: pd.DataFrame) -> None:
    """La légende donne l'effectif de chaque famille dans la sélection."""
    figure = carte.creer_carte(echantillon)
    total = sum(int(t.name.rsplit("(", 1)[1].rstrip(")").replace(" ", "")) for t in figure.data)
    assert total == len(carte.positions_valides(echantillon))
