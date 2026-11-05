"""Tests des constructeurs génériques de figures (`src/components/graphiques.py`)."""

import pandas as pd
import plotly.graph_objects as go

from src.components.graphiques import (
    LARGEUR_SOUS_TITRE,
    TextesFigure,
    appliquer_charte,
    barres_groupees,
    barres_horizontales,
    boites_quartiles,
    carte_chaleur,
    courbes,
    figure_vide,
    formater_effectif,
    histogramme,
)

TEXTES = TextesFigure("Titre", "Sous-titre", "Axe x", "Axe y")


def test_sous_titre_long_sur_plusieurs_lignes() -> None:
    """Un sous-titre trop long est coupé en lignes, la marge haute s'agrandit."""
    long = "mot " * LARGEUR_SOUS_TITRE
    figure = appliquer_charte(go.Figure(), TextesFigure("Titre", long))
    assert "<br>" in figure.layout.title.subtitle.text
    assert figure.layout.margin.t > 64


def test_figure_vide_affiche_un_message() -> None:
    """La figure vide garde le titre et affiche un message explicatif."""
    figure = figure_vide("Titre", "Rien à afficher")
    assert figure.layout.title.text == "Titre"
    assert figure.layout.annotations[0].text == "Rien à afficher"


def test_formater_effectif() -> None:
    """Les milliers sont séparés par une espace."""
    assert formater_effectif(250726) == "250 726"


def test_carte_chaleur_ecrit_les_pourcentages() -> None:
    """Chaque case affiche son pourcentage ; un tableau vide donne la figure vide."""
    valeurs = pd.DataFrame({"A": [60.0, 40.0]}, index=["x", "y"])
    effectifs = pd.DataFrame({"A": [60, 40]}, index=["x", "y"])
    figure = carte_chaleur(valeurs, effectifs, TEXTES)
    assert list(figure.data[0].text.ravel()) == ["60 %", "40 %"]
    assert carte_chaleur(valeurs.iloc[0:0], effectifs, TEXTES).layout.annotations


def test_boites_quartiles_utilise_les_quartiles() -> None:
    """La boîte est construite à partir des quartiles fournis."""
    resume = pd.DataFrame({
        "groupe": ["a"], "operations": [100], "p10": [1.0], "q1": [2.0],
        "mediane": [3.0], "q3": [4.0], "p90": [5.0],
    })
    boite = boites_quartiles(resume, "groupe", TEXTES).data[0]
    assert (boite.q1[0], boite.median[0], boite.q3[0]) == (2.0, 3.0, 4.0)


def test_histogramme_classes_de_largeur_fixe() -> None:
    """Les classes ont la largeur et les bornes demandées."""
    figure = histogramme(pd.Series([0.2, 1.4, 2.8]), TEXTES, (0, 3, 0.5))
    assert figure.data[0].xbins.size == 0.5
    assert list(figure.layout.xaxis.range) == [0, 3]


def test_courbes_une_trace_par_serie() -> None:
    """Une courbe par valeur de la colonne série."""
    donnees = pd.DataFrame({"x": [1, 2, 1, 2], "y": [5, 6, 7, 8], "s": ["a", "a", "b", "b"]})
    figure = courbes(donnees, ("x", "y", "s"), {"a": "#000000"}, TEXTES)
    assert [trace.name for trace in figure.data] == ["a", "b"]


def test_barres_horizontales_triees_avec_marge() -> None:
    """Barres triées par valeur, axe élargi pour que les étiquettes restent visibles."""
    donnees = pd.DataFrame({"cat": ["a", "b"], "val": [10.0, 2.0]})
    figure = barres_horizontales(donnees, ("cat", "val"), TEXTES)
    assert list(figure.data[0].y) == ["b", "a"]
    assert figure.layout.xaxis.range[1] > 10


def test_barres_horizontales_ordre_conserve() -> None:
    """Avec trier=False, la première ligne du tableau reste en haut."""
    donnees = pd.DataFrame({"cat": ["près", "loin"], "val": [1.0, 9.0]})
    figure = barres_horizontales(donnees, ("cat", "val"), TEXTES, trier=False)
    assert list(figure.data[0].y) == ["loin", "près"]


def test_barres_groupees_une_serie_par_ligne() -> None:
    """Une série de barres par ligne du tableau."""
    valeurs = pd.DataFrame({"Zone A": [5.0, 1.0]}, index=["Blessés", "Décès"])
    figure = barres_groupees(valeurs, TEXTES, {})
    assert [trace.name for trace in figure.data] == ["Blessés", "Décès"]
