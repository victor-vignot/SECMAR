
"""Page principale du tableau de bord SECMAR."""

import pandas as pd
from dash import Input, Output, html

from src.components.carte import creer_carte, creer_section_carte
from src.components.filters import creer_panneau_filtres
from src.components.kpi import creer_carte_kpi
from src.components.theme import (
    COULEUR_ORANGE,
    COULEUR_TEXTE,
    COULEUR_TURQUOISE,
    FOND_PAGE,
)
from src.utils.queries import (
    charger_donnees_dashboard,
    charger_options_filtres,
)


# Charge les valeurs proposées dans les filtres.
zones, evenements = charger_options_filtres()


# Construit la page principale du tableau de bord.
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

            creer_panneau_filtres(zones, evenements),

            html.Section(
                style={
                    "display": "grid",
                    "gridTemplateColumns": "repeat(5, minmax(0, 1fr))",
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

            creer_section_carte(),
        ],
    )


# Met à jour les indicateurs et la carte selon les filtres.
def enregistrer_callbacks(app):
    @app.callback(
        Output("kpi-operations", "children"),
        Output("kpi-personnes", "children"),
        Output("kpi-blesses", "children"),
        Output("kpi-deces", "children"),
        Output("kpi-duree", "children"),
        Output("graphique-carte", "figure"),
        Input("filtre-periode", "value"),
        Input("filtre-zone", "value"),
        Input("filtre-evenement", "value"),
    )
    def mettre_a_jour_dashboard(periode, zone, evenement):
        annee_debut, annee_fin = periode

        donnees = charger_donnees_dashboard(
            annee_debut=annee_debut,
            annee_fin=annee_fin,
            zone=zone,
            evenement=evenement,
        )

        operations = donnees["operations"]

        nombre_operations = operations["operation_id"].nunique()

        personnes = operations[
            "nombre_personnes_secourues"
        ].sum(min_count=1)

        blesses = operations[
            "nombre_personnes_blessees"
        ].sum(min_count=1)

        deces = operations[
            "nombre_personnes_decedees"
        ].sum(min_count=1)

        durees = pd.to_numeric(
            operations["duree_heures"],
            errors="coerce",
        )

        durees_valides = durees[durees.between(0, 24)]
        duree_mediane = durees_valides.median()

        if pd.notna(duree_mediane):
            total_minutes = round(duree_mediane * 60)
            heures, minutes = divmod(total_minutes, 60)
            texte_duree = f"{heures} h {minutes:02d} min"
        else:
            texte_duree = "N/D"

        def formater_total(valeur):
            if pd.isna(valeur):
                return "N/D"
            return f"{valeur:,.0f}".replace(",", " ")

        carte = operations.dropna(
            subset=["latitude", "longitude"]
        ).copy()

        carte = carte[
            carte["latitude"].between(-90, 90)
            & carte["longitude"].between(-180, 180)
        ]

        figure_carte = creer_carte(carte)

        return (
            formater_total(nombre_operations),
            formater_total(personnes),
            formater_total(blesses),
            formater_total(deces),
            texte_duree,
            figure_carte,
        )
