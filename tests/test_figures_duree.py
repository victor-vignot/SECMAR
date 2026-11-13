"""Tests des figures de l'onglet « Durée et distance »."""

import pandas as pd

from src.components import figures_duree


def test_histogramme_limite_a_la_plage_affichee(echantillon: pd.DataFrame) -> None:
    """L'histogramme exclut les distances nulles et au-delà de 30 milles."""
    valeurs = pd.Series(figures_duree.figure_distance_cote(echantillon).data[0].x)
    assert valeurs.gt(0).all()
    assert valeurs.le(30).all()


def test_gravite_distance_dans_l_ordre_des_classes() -> None:
    """Les classes restent dans l'ordre : trait de côte en haut, large en bas."""
    donnees = pd.DataFrame({
        "distance_cote_mn": [0.0, 0.2, 1.0, 5.0, 20.0, 900.0],
        "personnes_decedees": [1, 0, 0, 0, 1, 0],
        "personnes_disparues": [0, 0, 0, 0, 0, 1],
    })
    barres = figures_duree.figure_gravite_distance(donnees).data[0]
    # Plotly trace de bas en haut : le trait de côte est le dernier élément.
    assert list(barres.y) == [
        "Plus de 200 milles (opérations lointaines)", "12 à 200 milles",
        "3 à 12 milles", "0,5 à 3 milles",
        "Moins de 0,5 mille", "Au trait de côte",
    ]


def test_histogramme_graduations_en_entier(echantillon: pd.DataFrame) -> None:
    """L'axe logarithmique écrit « 10 000 » et non « 10k »."""
    figure = figures_duree.figure_distance_cote(echantillon)
    assert figure.layout.yaxis.exponentformat == "none"


def test_famille_distance_lignes_a_100(echantillon: pd.DataFrame) -> None:
    """Une ligne par famille, une colonne par classe de distance, chaque ligne à 100 %."""
    figure = figures_duree.figure_famille_distance(echantillon)
    lignes = pd.DataFrame(figure.data[0].z).sum(axis=1)
    assert ((lignes - 100).abs() < 1e-6).all()
    assert figure.data[0].x[0] == "Au trait de côte"
