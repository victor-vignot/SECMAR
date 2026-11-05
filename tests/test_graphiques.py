"""Tests des constructeurs génériques de figures (`src/components/graphiques.py`)."""

import pandas as pd
import plotly.graph_objects as go

from src.components.graphiques import (
    LARGEUR_SOUS_TITRE,
    TextesFigure,
    appliquer_charte,
    carte_chaleur,
    figure_vide,
    formater_effectif,
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
