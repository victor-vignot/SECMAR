"""Carte géographique des opérations (représentation géolocalisée)."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html

from config import MAX_POINTS_CARTE
from src.components.theme import COULEURS_FAMILLES, LAYOUT_GRAPHIQUE, STYLE_FOND_CARTE
from src.utils.familles import ORDRE_FAMILLES


def preparer_points_carte(donnees: pd.DataFrame) -> pd.DataFrame:
    """Garde les positions valides et limite le nombre de points affichés."""
    points = donnees.dropna(subset=["latitude", "longitude"])
    points = points[
        points["latitude"].between(-90, 90)
        & points["longitude"].between(-180, 180)
        # Les positions (0, 0) sont des valeurs par défaut, pas des lieux réels.
        & ~(points["latitude"].eq(0) & points["longitude"].eq(0))
    ]
    if len(points) > MAX_POINTS_CARTE:
        # Échantillon reproductible pour garder une carte fluide.
        points = points.sample(n=MAX_POINTS_CARTE, random_state=42)
    return points


def decrire_positions(donnees: pd.DataFrame) -> str:
    """Phrase indiquant combien d'opérations ne figurent pas sur la carte."""
    sans_position = int(donnees["latitude"].isna().sum())
    if sans_position == 0:
        return "Toutes les opérations de la sélection ont une position."
    part = sans_position / len(donnees) * 100
    nombre = f"{sans_position:,}".replace(",", " ")
    return (
        f"{nombre} opérations de la sélection ({part:.0f} %) n'ont pas de position "
        "fiable (position absente, à (0, 0) ou à plus de 5 km dans les terres) : "
        "elles comptent dans les indicateurs mais pas sur la carte."
    )


def creer_carte(donnees: pd.DataFrame) -> go.Figure:
    """Crée la carte des opérations, colorées par famille d'événements."""
    points = preparer_points_carte(donnees)
    figure = px.scatter_map(
        points,
        lat="latitude",
        lon="longitude",
        color="famille",
        color_discrete_map=COULEURS_FAMILLES,
        category_orders={"famille": ORDRE_FAMILLES},
        hover_data={
            "operation_id": True,
            "cross": True,
            "annee": True,
            "latitude": False,
            "longitude": False,
        },
        labels={
            "famille": "Famille d'événements",
            "operation_id": "N° d'opération",
            "cross": "CROSS",
            "annee": "Année",
        },
        map_style=STYLE_FOND_CARTE,
        zoom=4.3,
        center={"lat": 46.5, "lon": 2.5},
    )
    figure.update_traces(marker={"size": 6, "opacity": 0.7})
    figure.update_layout(
        height=520,
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        paper_bgcolor=LAYOUT_GRAPHIQUE["paper_bgcolor"],
        font=LAYOUT_GRAPHIQUE["font"],
        legend={"title": {"text": "Famille d'événements"}, "itemsizing": "constant"},
    )
    return figure


def creer_section_carte() -> html.Section:
    """Construit la section contenant la carte."""
    return html.Section(
        className="panneau panneau-carte",
        children=[
            html.H2("Où ont lieu les opérations ?", className="titre-section"),
            dcc.Graph(id="graphique-carte", config={"displayModeBar": False}),
            html.P(id="note-carte", className="legende legende-forte"),
            html.P(
                f"Chaque point est une opération (au plus {MAX_POINTS_CARTE:,} points "
                "tirés au hasard pour garder la carte fluide). Cliquer sur une famille "
                "dans la légende pour l'afficher ou la masquer.".replace(",", " "),
                className="legende",
            ),
        ],
    )
