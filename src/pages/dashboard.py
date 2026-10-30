"""Page principale du tableau de bord SECMAR."""

import pandas as pd
from dash import Input, Output, dcc, html

from config import ANNEE_MAX, ANNEE_MIN
from src.components.carte import creer_carte, creer_section_carte
from src.components.filters import creer_panneau_filtres
from src.components.graphiques import (
    creer_graphique_annuel,
    creer_graphique_conditions,
    creer_graphique_durees,
    creer_graphique_evenements,
    creer_graphique_evenements_detailles,
)
from src.components.kpi import creer_carte_kpi
from src.components.theme import (
    COULEUR_ORANGE,
    COULEUR_TEXTE,
    COULEUR_TURQUOISE,
    FOND_PAGE,
    STYLE_CARTE,
)
from src.utils.queries import (
    charger_donnees_dashboard,
    charger_options_filtres,
)


# Charge les valeurs proposées dans les filtres.
zones, evenements = charger_options_filtres()


# Construit la page complète du tableau de bord.
def creer_page_dashboard():
    return html.Div(
        style={
            "fontFamily": "Arial, sans-serif",
            "backgroundColor": FOND_PAGE,
            "color": COULEUR_TEXTE,
            "minHeight": "100vh",
            "padding": "32px 5%",
        },
        children=[
            html.Header(
                style={
                    "borderBottom": f"3px solid {COULEUR_ORANGE}",
                    "paddingBottom": "22px",
                    "marginBottom": "28px",
                    "backgroundColor": FOND_PAGE,
                },
                children=[
                    html.H1(
                        "SECMAR",
                        style={
                            "fontSize": "32px",
                            "fontWeight": "800",
                            "color": COULEUR_ORANGE,
                            "margin": "0",
                        },
                    ),
                    html.P(
                        "Observatoire des opérations de secours en mer",
                        style={"color": "#64748B"},
                    ),
                ],
            ),

            # Affiche les filtres de période, de CROSS et d'événement.
            creer_panneau_filtres(zones, evenements),

            # Affiche les cinq indicateurs clés.
            html.Section(
                style={
                    "display": "grid",
                    "gridTemplateColumns": (
                        "repeat(5, minmax(0, 1fr))"
                    ),
                    "gap": "16px",
                    "marginBottom": "28px",
                },
                children=[
                    creer_carte_kpi(
                        "Opérations recensées",
                        "kpi-operations",
                        "Nombre d'opérations distinctes",
                        COULEUR_ORANGE,
                    ),
                    creer_carte_kpi(
                        "Personnes secourues",
                        "kpi-personnes",
                        "Total déclaré dans les statistiques",
                        COULEUR_TURQUOISE,
                    ),
                    creer_carte_kpi(
                        "Personnes blessées",
                        "kpi-blesses",
                        "Total déclaré dans les statistiques",
                        COULEUR_ORANGE,
                    ),
                    creer_carte_kpi(
                        "Personnes décédées",
                        "kpi-deces",
                        "Total déclaré dans les statistiques",
                        "#6B3FA0",
                    ),
                    creer_carte_kpi(
                        "Durée médiane",
                        "kpi-duree",
                        "Opérations de 0 à 24 heures",
                        COULEUR_ORANGE,
                    ),
                ],
            ),

            # Affiche la carte et le choix de son mode.
            creer_section_carte(),

            # Compare l'évolution annuelle et les types d'événements.
            html.Section(
                style={
                    "display": "grid",
                    "gridTemplateColumns": "repeat(2, minmax(0, 1fr))",
                    "gap": "24px",
                    "marginBottom": "28px",
                },
                children=[
                    html.Div(
                        style=STYLE_CARTE,
                        children=[
                            html.H2("Évolution annuelle"),
                            dcc.Graph(id="graphique-annuel"),
                        ],
                    ),
                    html.Div(
                        style=STYLE_CARTE,
                        children=[
                            html.H2("Types d'événements"),
                            dcc.RadioItems(
                                id="mode-evenements",
                                options=[
                                    {
                                        "label": "Catégories",
                                        "value": "categories",
                                    },
                                    {
                                        "label": "Événements détaillés",
                                        "value": "details",
                                    },
                                ],
                                value="categories",
                                inline=True,
                                labelStyle={
                                    "display": "inline-block",
                                    "marginRight": "18px",
                                    "marginBottom": "12px",
                                    "cursor": "pointer",
                                },
                                inputStyle={"marginRight": "6px"},
                            ),
                            dcc.Graph(id="graphique-evenements"),
                        ],
                    ),
                ],
            ),

            # Affiche les conditions maritimes et les durées.
            html.Section(
                style={
                    "display": "grid",
                    "gridTemplateColumns": "repeat(2, minmax(0, 1fr))",
                    "gap": "24px",
                    "marginBottom": "28px",
                },
                children=[
                    html.Div(
                        style=STYLE_CARTE,
                        children=[
                            html.H2("Conditions maritimes"),
                            dcc.Graph(id="graphique-conditions"),
                        ],
                    ),
                    html.Div(
                        style=STYLE_CARTE,
                        children=[
                            html.H2("Durée des opérations"),
                            dcc.Graph(id="graphique-durees"),
                            html.P(
                                "Histogramme limité aux durées de "
                                "0 à 24 heures.",
                                style={
                                    "fontSize": "12px",
                                    "color": "#64748B",
                                },
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


# Met à jour les indicateurs et graphiques selon les filtres.
def enregistrer_callbacks(app):
    @app.callback(
        Output("kpi-operations", "children"),
        Output("kpi-personnes", "children"),
        Output("kpi-blesses", "children"),
        Output("kpi-deces", "children"),
        Output("kpi-duree", "children"),
        Output("graphique-carte", "figure"),
        Output("graphique-annuel", "figure"),
        Output("graphique-evenements", "figure"),
        Output("graphique-conditions", "figure"),
        Output("graphique-durees", "figure"),
        Input("filtre-periode", "value"),
        Input("filtre-zone", "value"),
        Input("filtre-evenement", "value"),
        Input("mode-carte", "value"),
        Input("mode-evenements", "value"),
    )
    def mettre_a_jour_dashboard(
        periode,
        zone,
        evenement,
        mode_carte,
        mode_evenements,
    ):
        # Récupère les années sélectionnées.
        annee_debut, annee_fin = periode

        donnees = charger_donnees_dashboard(
            annee_debut=annee_debut,
            annee_fin=annee_fin,
            zone=zone,
            evenement=evenement,
        )

        operations = donnees["operations"]

        # Compte les opérations distinctes.
        nombre_operations = operations["operation_id"].nunique()

        # Additionne les indicateurs humains disponibles.
        personnes = operations[
            "nombre_personnes_secourues"
        ].sum(min_count=1)
        blesses = operations[
            "nombre_personnes_blessees"
        ].sum(min_count=1)
        deces = operations[
            "nombre_personnes_decedees"
        ].sum(min_count=1)

        # Calcule la durée médiane des opérations valides.
        durees = pd.to_numeric(
            operations["duree_heures"],
            errors="coerce",
        )
        durees_valides = durees[durees.between(0, 24)]
        duree_mediane = durees_valides.median()

        # Affiche la durée en heures et minutes.
        if pd.notna(duree_mediane):
            total_minutes = round(duree_mediane * 60)
            heures, minutes = divmod(total_minutes, 60)
            texte_duree = f"{heures} h {minutes:02d} min"
        else:
            texte_duree = "N/D"

        # Formate les nombres sans décimales.
        def formater_total(valeur):
            if pd.isna(valeur):
                return "N/D"
            return f"{valeur:,.0f}".replace(",", " ")

        # Garde uniquement les coordonnées valides pour la carte.
        carte = operations.dropna(
            subset=["latitude", "longitude"]
        ).copy()
        carte = carte[
            carte["latitude"].between(-90, 90)
            & carte["longitude"].between(-180, 180)
        ]

        figure_carte = creer_carte(carte, mode=mode_carte)

        # Reconstruit les graphiques avec les filtres actifs.
        figure_annuelle = creer_graphique_annuel(
            donnees["annuel"]
        )

        if mode_evenements == "details":
            figure_evenements = creer_graphique_evenements_detailles(
                donnees["evenements_detailles"]
            )
        else:
            figure_evenements = creer_graphique_evenements(
                donnees["evenements"]
            )

        figure_conditions = creer_graphique_conditions(
            operations
        )
        figure_durees = creer_graphique_durees(
            operations
        )

        return (
            formater_total(nombre_operations),
            formater_total(personnes),
            formater_total(blesses),
            formater_total(deces),
            texte_duree,
            figure_carte,
            figure_annuelle,
            figure_evenements,
            figure_conditions,
            figure_durees,
        )