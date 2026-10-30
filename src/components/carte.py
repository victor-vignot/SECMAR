"""Composants de la carte géographique des opérations."""

import plotly.express as px
from dash import dcc, html

from config import MAX_POINTS_CARTE
from src.components.theme import (
    COULEUR_ORANGE,
    COULEUR_TURQUOISE,
    STYLE_CARTE,
)


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


# Crée une carte de densité ou une carte des opérations individuelles.
def creer_carte(donnees, mode="densite"):
    donnees = donnees.dropna(subset=["latitude", "longitude"]).copy()

    # Écarte les coordonnées impossibles avant de tracer la carte.
    donnees = donnees[
        donnees["latitude"].between(-90, 90)
        & donnees["longitude"].between(-180, 180)
    ]

    if mode == "operations":
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
        figure.update_traces(marker={"size": 8, "opacity": 0.75})

    else:
        figure = px.density_map(
            donnees,
            lat="latitude",
            lon="longitude",
            radius=8,
            map_style="carto-positron",
            zoom=3,
            center={"lat": 46.5, "lon": 2.5},
            color_continuous_scale=[
                "#E8F6F5",
                COULEUR_TURQUOISE,
                COULEUR_ORANGE,
            ],
        )

    figure.update_layout(
        height=480,
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        legend_title_text="Type d'événement",
    )

    return figure


# Construit la section de carte et son sélecteur de mode.
def creer_section_carte():
    return html.Section(
        style={**STYLE_CARTE, "marginBottom": "24px"},
        children=[
            html.H2(
                "Répartition géographique des opérations",
                style={"fontSize": "19px", "marginTop": "0"},
            ),
            html.P(
                "Explore les concentrations ou les opérations individuelles.",
                style={"color": "#64748B", "fontSize": "14px"},
            ),
            dcc.RadioItems(
                id="mode-carte",
                options=[
                    {
                        "label": "Zones de concentration",
                        "value": "densite",
                    },
                    {
                        "label": "Opérations individuelles",
                        "value": "operations",
                    },
                ],
                value="densite",
                inline=True,
                labelStyle={
                    "display": "inline-block",
                    "marginRight": "20px",
                    "marginBottom": "12px",
                    "cursor": "pointer",
                },
                inputStyle={"marginRight": "6px"},
            ),
            dcc.Graph(
                id="graphique-carte",
                config={"displayModeBar": False},
            ),
        ],
    )