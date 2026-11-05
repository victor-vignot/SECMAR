"""Constructeurs génériques de figures Plotly.

Chaque fonction reçoit un tableau déjà agrégé (voir `src/utils/aggregations.py`)
et applique la charte commune. Les figures de chaque onglet (modules
`figures_*.py`) s'appuient sur ces constructeurs.
"""

import textwrap
from dataclasses import dataclass

import plotly.graph_objects as go

from src.components.theme import (
    COULEUR_SECONDAIRE,
    LAYOUT_GRAPHIQUE,
)

# Au-delà de cette longueur, le sous-titre passe sur deux lignes (sinon il est coupé).
LARGEUR_SOUS_TITRE = 85


@dataclass(frozen=True)
class TextesFigure:
    """Textes d'une figure : titre, sous-titre et libellés des axes."""

    titre: str
    sous_titre: str = ""
    libelle_x: str = ""
    libelle_y: str = ""


def appliquer_charte(figure: go.Figure, textes: TextesFigure) -> go.Figure:
    """Applique la mise en page commune, le titre et le sous-titre.

    Un sous-titre long est coupé en lignes, et la marge haute agrandie d'autant.
    """
    lignes = textwrap.wrap(textes.sous_titre, LARGEUR_SOUS_TITRE) or [""]
    figure.update_layout(**LAYOUT_GRAPHIQUE)
    figure.update_layout(
        title={"text": textes.titre, "subtitle": {"text": "<br>".join(lignes)}},
        margin={"t": LAYOUT_GRAPHIQUE["margin"]["t"] + 16 * (len(lignes) - 1)},
    )
    return figure


def figure_vide(titre: str, message: str = "Aucune opération pour ces filtres") -> go.Figure:
    """Figure affichée quand la sélection ne contient pas assez de données."""
    figure = go.Figure()
    figure.add_annotation(
        text=message, showarrow=False, font={"size": 14, "color": COULEUR_SECONDAIRE},
        xref="paper", yref="paper", x=0.5, y=0.5,
    )
    figure.update_xaxes(visible=False)
    figure.update_yaxes(visible=False)
    return appliquer_charte(figure, TextesFigure(titre))


def formater_effectif(nombre: float) -> str:
    """Formate un effectif avec une espace comme séparateur de milliers."""
    return f"{nombre:,.0f}".replace(",", " ")
