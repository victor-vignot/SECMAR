
"""Composant réutilisable pour afficher un indicateur clé."""

from dash import html

from src.components.theme import COULEUR_SECONDAIRE, STYLE_CARTE


# Crée une carte KPI avec un titre, une valeur et une description.
def creer_carte_kpi(titre, identifiant, description, couleur):
    return html.Div(
        style=STYLE_CARTE,
        children=[
            html.P(
                titre,
                style={
                    "color": COULEUR_SECONDAIRE,
                    "fontSize": "14px",
                    "margin": "0 0 12px 0",
                },
            ),
            html.H2(
                "—",
                id=identifiant,
                style={
                    "color": couleur,
                    "fontSize": "30px",
                    "margin": "0 0 8px 0",
                },
            ),
            html.P(
                description,
                style={
                    "color": COULEUR_SECONDAIRE,
                    "fontSize": "12px",
                    "margin": "0",
                },
            ),
        ],
    )
