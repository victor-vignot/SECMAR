
"""Filtres de période, de CROSS et de catégorie d'événement."""

from dash import dcc, html

from config import ANNEE_MIN, ANNEE_MAX
from src.components.theme import COULEUR_SECONDAIRE, STYLE_CARTE

VALEUR_TOUTES = "toutes"


# Prépare les options d'une liste déroulante.
def _options_dropdown(valeurs, libelle_tout):
    options = [{"label": libelle_tout, "value": VALEUR_TOUTES}]
    options.extend(
        {"label": valeur, "value": valeur}
        for valeur in valeurs
    )
    return options


# Construit le panneau des trois filtres.
def creer_panneau_filtres(cross, evenements):
    return html.Section(
        style={**STYLE_CARTE, "marginBottom": "24px"},
        children=[
            html.H2(
                "Explorer les opérations",
                style={"fontSize": "18px", "marginTop": "0"},
            ),
            html.Div(
                style={
                    "display": "grid",
                    "gridTemplateColumns": (
                        "repeat(3, minmax(0, 1fr))"
                    ),
                    "gap": "20px",
                },
                children=[
                    html.Div([
                        html.Label("Période (années)"),
                        html.Div(
                            style={"paddingTop": "10px"},
                            children=dcc.RangeSlider(
                                id="filtre-periode",
                                min=ANNEE_MIN,
                                max=ANNEE_MAX,
                                step=1,
                                value=[ANNEE_MIN, ANNEE_MAX],
                                marks={
                                    annee: str(annee)
                                    for annee in range(
                                        ANNEE_MIN,
                                        ANNEE_MAX + 1,
                                        5,
                                    )
                                },
                                allowCross=False,
                            ),
                        ),
                    ]),
                    html.Div([
                        html.Label("CROSS"),
                        dcc.Dropdown(
                            id="filtre-zone",
                            options=_options_dropdown(
                                cross,
                                "Tous les CROSS",
                            ),
                            value=VALEUR_TOUTES,
                            clearable=False,
                            placeholder="Sélectionner un CROSS",
                        ),
                    ]),
                    html.Div([
                        html.Label("Type d'événement"),
                        dcc.Dropdown(
                            id="filtre-evenement",
                            options=_options_dropdown(
                                evenements,
                                "Tous les événements",
                            ),
                            value=VALEUR_TOUTES,
                            clearable=False,
                            placeholder="Sélectionner un événement",
                        ),
                    ]),
                ],
            ),
            html.P(
                "Les indicateurs et les graphiques suivent ces filtres.",
                style={
                    "fontSize": "12px",
                    "color": COULEUR_SECONDAIRE,
                    "marginTop": "16px",
                    "marginBottom": "0",
                },
            ),
        ],
    )
