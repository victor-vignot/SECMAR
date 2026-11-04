
"""Composants de la carte géographique des opérations."""

import plotly.express as px
from dash import dcc, html

from config import MAX_POINTS_CARTE
from src.components.theme import STYLE_CARTE


# Couleurs attribuées aux catégories originales des événements.
COULEURS_EVENEMENTS = {
    "Fausses alertes": "#2EAD62",
    "Autres affaires nécessitant opération": "#3498DB",
    "Avaries non suivies d'accident navire": "#F1C40F",
    "Accidents de navire": "#F28C28",
    "Accidents individuels à personnes non embarquées": "#FF6B6B",
    "Accidents individuels à personnes embarquées": "#E53935",
    "Accidents individuels à personnes": "#8B0000",
}


# Crée la carte des opérations individuelles.
def creer_carte(donnees):
    donnees = donnees.dropna(
        subset=["latitude", "longitude"]
    ).copy()

    # Écarte les coordonnées impossibles avant de tracer la carte.
    donnees = donnees[
        donnees["latitude"].between(-90, 90)
        & donnees["longitude"].between(-180, 180)
    ]

    # Limite le nombre de points pour garder une carte fluide.
    if len(donnees) > MAX_POINTS_CARTE:
        donnees = donnees.sample(
            n=MAX_POINTS_CARTE,
            random_state=42,
        )

    figure = px.scatter_map(
        donnees,
        lat="latitude",
        lon="longitude",
        color="categorie_evenement",
        color_discrete_map=COULEURS_EVENEMENTS,
        hover_data={
            "operation_id": True,
            "cross": True,
            "latitude": False,
            "longitude": False,
        },
        map_style="carto-positron",
        zoom=3,
        center={"lat": 46.5, "lon": 2.5},
        labels={
            "categorie_evenement": "Type d'événement",
            "operation_id": "N° d'opération",
            "cross": "CROSS",
        },
    )

    figure.update_traces(
        marker={"size": 8, "opacity": 0.75}
    )

    figure.update_layout(
        height=480,
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        legend_title_text="Type d'événement",
    )

    return figure


# Construit la section contenant la carte.
def creer_section_carte():
    return html.Section(
        style={**STYLE_CARTE, "marginBottom": "24px"},
        children=[
            html.H2(
                "Répartition géographique des opérations",
                style={"fontSize": "19px", "marginTop": "0"},
            ),
            html.P(
                "Chaque point représente une opération de secours.",
                style={"color": "#64748B", "fontSize": "14px"},
            ),
            dcc.Graph(
                id="graphique-carte",
                config={"displayModeBar": False},
            ),
        ],
    )
