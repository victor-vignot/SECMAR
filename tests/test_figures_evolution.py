"""Tests des figures de l'onglet « Évolution »."""

from collections.abc import Callable

import pandas as pd
import plotly.graph_objects as go
import pytest

from src.components import figures_evolution

type FabriqueFigure = Callable[[pd.DataFrame], go.Figure]

FIGURES = [
    figures_evolution.figure_bulles_animees,
    figures_evolution.figure_courbe_annuelle,
]


@pytest.fixture(name="grand_echantillon")
def fixture_grand_echantillon(echantillon: pd.DataFrame) -> pd.DataFrame:
    """L'échantillon répété 10 fois : assez d'opérations par famille et par an."""
    return pd.concat([echantillon] * 10, ignore_index=True)


@pytest.mark.parametrize("fonction", FIGURES, ids=lambda f: f.__name__)
def test_figure_avec_titre_et_donnees(
    fonction: FabriqueFigure, grand_echantillon: pd.DataFrame
) -> None:
    """Chaque figure a un titre et au moins une série de données."""
    figure = fonction(grand_echantillon)
    assert isinstance(figure, go.Figure)
    assert figure.layout.title.text
    assert len(figure.data) >= 1


@pytest.mark.parametrize("fonction", FIGURES, ids=lambda f: f.__name__)
def test_une_seule_annee(fonction: FabriqueFigure, echantillon: pd.DataFrame) -> None:
    """Avec une seule année, la figure invite à élargir la période."""
    une_annee = echantillon[echantillon["annee"] == 2015]
    assert fonction(une_annee).layout.annotations


def test_ruptures_grisees(echantillon: pd.DataFrame) -> None:
    """Les deux périodes de rupture (2009-2010, 2019-2021) sont grisées."""
    figure = figures_evolution.figure_courbe_annuelle(echantillon)
    assert [forme.x0 for forme in figure.layout.shapes] == [2008.5, 2018.5]


def test_bulles_animees_une_image_par_annee(grand_echantillon: pd.DataFrame) -> None:
    """Une image d'animation par année, curseur et bouton de lecture présents."""
    figure = figures_evolution.figure_bulles_animees(grand_echantillon)
    assert len(figure.frames) == grand_echantillon["annee"].nunique()
    assert figure.layout.sliders[0].currentvalue.prefix == "Année : "
    assert figure.layout.legend.itemsizing == "constant"
    assert figure.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] == 700


def test_bulles_masquees_si_trop_peu_d_operations(echantillon: pd.DataFrame) -> None:
    """Moins de 30 opérations par famille et par an : rien de fiable à animer."""
    assert figures_evolution.figure_bulles_animees(echantillon.head(200)).layout.annotations


def test_famille_apparue_en_cours_de_periode() -> None:
    """Une famille absente la première année a quand même sa série animée."""
    lignes = (
        [(2010, "Médical")] * 40
        + [(2011, "Médical")] * 40
        + [(2011, "Sûreté et migrations")] * 40
    )
    donnees = pd.DataFrame(lignes, columns=["annee", "famille"]).assign(
        operation_id=range(120), personnes_decedees=0, personnes_disparues=0,
        personnes_impliquees_sans_clandestins=1,
    )
    figure = figures_evolution.figure_bulles_animees(donnees)
    assert {trace.name for trace in figure.data} == {"Médical", "Sûreté et migrations"}
