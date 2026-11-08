"""Tests des figures de l'onglet « Où ? »."""

import pandas as pd

from src.components import figures_ou


def test_cross_classes_du_plus_actif(echantillon: pd.DataFrame) -> None:
    """Le CROSS le plus actif est sur la première ligne de la carte de chaleur."""
    figure = figures_ou.figure_cross_famille(echantillon)
    assert figure.data[0].y[0] == echantillon["cross"].value_counts().index[0]


def test_departements_limites_aux_plus_actifs(echantillon: pd.DataFrame) -> None:
    """Au plus 15 départements sont affichés."""
    figure = figures_ou.figure_departement_famille(echantillon)
    assert len(figure.data[0].y) <= figures_ou.NOMBRE_DEPARTEMENTS
