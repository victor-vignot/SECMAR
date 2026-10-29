
# Importe les outils nécessaires pour l'interface, les données et les graphiques.
from dash import Dash, html, dcc
import pandas as pd
import plotly.express as px
import sqlite3

from config import DB_PATH


# Définit les couleurs principales du tableau de bord.
COULEUR_ORANGE = "#E8730C"
COULEUR_TURQUOISE = "#1FA7A0"
COULEUR_TEXTE = "#263238"
COULEUR_SECONDAIRE = "#64748B"
COULEUR_BORDURE = "#E5E7EB"


# Définit le style commun aux cartes de la page.
STYLE_CARTE = {
    "border": f"1px solid {COULEUR_BORDURE}",
    "borderRadius": "12px",
    "padding": "22px",
    "backgroundColor": "#FFFFFF",
}


# Crée une carte KPI réutilisable.
def creer_carte_kpi(titre, valeur, description, couleur):
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
                valeur,
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


# Charge les coordonnées des opérations pour la carte provisoire.
def charger_coordonnees():
    requete = """
        SELECT latitude, longitude
        FROM raw_operations
        WHERE latitude IS NOT NULL
          AND longitude IS NOT NULL
    """

    with sqlite3.connect(DB_PATH) as connexion:
        donnees = pd.read_sql_query(requete, connexion)

    donnees["latitude"] = pd.to_numeric(
        donnees["latitude"], errors="coerce"
    )
    donnees["longitude"] = pd.to_numeric(
        donnees["longitude"], errors="coerce"
    )
    donnees = donnees.dropna(subset=["latitude", "longitude"])

    donnees = donnees[
        donnees["latitude"].between(-90, 90)
        & donnees["longitude"].between(-180, 180)
    ]

    # Limite l'échantillon pour conserver un affichage fluide.
    if len(donnees) > 30000:
        donnees = donnees.sample(n=30000, random_state=42)

    return donnees


# Crée une carte de densité par cellules, sans fond de carte externe.
def creer_carte_densite():
    donnees = charger_coordonnees()

    figure = px.density_heatmap(
        donnees,
        x="longitude",
        y="latitude",
        nbinsx=180,
        nbinsy=90,
        color_continuous_scale=[
            "#E8F6F5",
            COULEUR_TURQUOISE,
            COULEUR_ORANGE,
        ],
    )

    figure.update_layout(
        margin={"l": 10, "r": 10, "t": 10, "b": 10},
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        height=450,
        xaxis_title="Longitude",
        yaxis_title="Latitude",
        coloraxis_colorbar_title="Densité",
    )
    figure.update_xaxes(showgrid=True, gridcolor=COULEUR_BORDURE)
    figure.update_yaxes(showgrid=True, gridcolor=COULEUR_BORDURE)

    return figure


# Calcule le nombre d'opérations recensées chaque année.
def creer_graphique_annuel():
    requete = """
        SELECT annee, COUNT(*) AS nombre_operations
        FROM raw_operations_stats
        WHERE annee BETWEEN 2005 AND 2025
        GROUP BY annee
        ORDER BY annee
    """

    with sqlite3.connect(DB_PATH) as connexion:
        donnees = pd.read_sql_query(requete, connexion)

    figure = px.line(
        donnees,
        x="annee",
        y="nombre_operations",
        markers=True,
        labels={
            "annee": "Année",
            "nombre_operations": "Nombre d'opérations",
        },
    )

    # Applique la couleur principale au graphique annuel.
    figure.update_traces(
        line={"color": COULEUR_ORANGE, "width": 3},
        marker={"color": COULEUR_ORANGE, "size": 7},
    )
    figure.update_layout(
        height=330,
        margin={"l": 10, "r": 10, "t": 20, "b": 10},
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
    )
    figure.update_xaxes(dtick=2, gridcolor=COULEUR_BORDURE)
    figure.update_yaxes(gridcolor=COULEUR_BORDURE)

    return figure


# Classe les principales catégories d'événements par nombre d'opérations.
def creer_graphique_evenements():
    requete = """
        SELECT categorie_evenement, COUNT(*) AS nombre_operations
        FROM raw_operations
        WHERE categorie_evenement IS NOT NULL
        GROUP BY categorie_evenement
        ORDER BY nombre_operations DESC
    """

    with sqlite3.connect(DB_PATH) as connexion:
        donnees = pd.read_sql_query(requete, connexion)

    # Garde les huit catégories les plus fréquentes pour la lisibilité.
    donnees = donnees.head(8).sort_values("nombre_operations")

    figure = px.bar(
        donnees,
        x="nombre_operations",
        y="categorie_evenement",
        orientation="h",
        labels={
            "nombre_operations": "Nombre d'opérations",
            "categorie_evenement": "Catégorie",
        },
        color_discrete_sequence=[COULEUR_TURQUOISE],
    )

    figure.update_layout(
        height=330,
        margin={"l": 10, "r": 10, "t": 20, "b": 10},
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        yaxis_title=None,
    )
    figure.update_xaxes(gridcolor=COULEUR_BORDURE)
    figure.update_yaxes(showgrid=False)

    return figure


# Compare les niveaux de vent et l'état de la mer.
def creer_graphique_conditions():
    requete = """
        SELECT vent_force, mer_force
        FROM raw_operations
    """

    with sqlite3.connect(DB_PATH) as connexion:
        donnees = pd.read_sql_query(requete, connexion)

    # Convertit les valeurs en nombres et ignore les données manquantes.
    donnees["vent_force"] = pd.to_numeric(
        donnees["vent_force"], errors="coerce"
    )
    donnees["mer_force"] = pd.to_numeric(
        donnees["mer_force"], errors="coerce"
    )

    # Compte le nombre d'opérations pour chaque niveau de vent et de mer.
    vent = donnees["vent_force"].value_counts().sort_index()
    mer = donnees["mer_force"].value_counts().sort_index()

    figure = px.bar(
        x=vent.index.astype(str),
        y=vent.values,
        labels={"x": "Niveau", "y": "Nombre d'opérations"},
        color_discrete_sequence=[COULEUR_ORANGE],
    )
    figure.update_traces(name="Force du vent", showlegend=True)

    # Ajoute l'état de la mer comme deuxième série.
    figure.add_bar(
        x=mer.index.astype(str),
        y=mer.values,
        name="État de la mer",
        marker_color=COULEUR_TURQUOISE,
    )

    figure.update_layout(
        barmode="group",
        height=330,
        margin={"l": 10, "r": 10, "t": 20, "b": 10},
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        legend_title_text="Conditions",
    )

    return figure


# Calcule les durées et prépare leur histogramme.
def creer_graphique_durees():
    requete = """
        SELECT
            date_heure_reception_alerte,
            date_heure_fin_operation
        FROM raw_operations
        WHERE date_heure_reception_alerte IS NOT NULL
          AND date_heure_fin_operation IS NOT NULL
    """

    with sqlite3.connect(DB_PATH) as connexion:
        donnees = pd.read_sql_query(requete, connexion)

    debut = pd.to_datetime(
        donnees["date_heure_reception_alerte"],
        errors="coerce",
        utc=True,
    )
    fin = pd.to_datetime(
        donnees["date_heure_fin_operation"],
        errors="coerce",
        utc=True,
    )

    donnees["duree_heures"] = (fin - debut).dt.total_seconds() / 3600

    # Limite provisoirement l'histogramme aux durées entre 0 et 24 heures.
    durees = donnees.loc[
        donnees["duree_heures"].between(0, 24),
        "duree_heures",
    ].dropna()

    figure = px.histogram(
        durees,
        x="duree_heures",
        nbins=24,
        labels={
            "duree_heures": "Durée (heures)",
            "count": "Nombre d'opérations",
        },
        color_discrete_sequence=[COULEUR_TURQUOISE],
    )

    figure.update_layout(
        height=330,
        margin={"l": 10, "r": 10, "t": 20, "b": 10},
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
    )

    return figure


# Initialise l'application web Dash.
app = Dash(__name__)


# Organise toutes les sections de la page de haut en bas.
app.layout = html.Div(
    style={
        "fontFamily": "Arial, sans-serif",
        "backgroundColor": "#FFFFFF",
        "color": COULEUR_TEXTE,
        "minHeight": "100vh",
        "padding": "32px 5%",
    },
    children=[
        # Présente le titre et le sous-titre du tableau de bord.
        html.Header(
            style={
                "borderBottom": f"3px solid {COULEUR_ORANGE}",
                "paddingBottom": "22px",
                "marginBottom": "28px",
            },
            children=[
                html.Div(
                    "SECMAR",
                    style={
                        "fontSize": "32px",
                        "fontWeight": "800",
                        "letterSpacing": "1px",
                        "color": COULEUR_ORANGE,
                    },
                ),
                html.P(
                    "Observatoire des opérations de secours en mer",
                    style={
                        "fontSize": "15px",
                        "color": COULEUR_SECONDAIRE,
                        "marginBottom": "0",
                    },
                ),
            ],
        ),

        # Regroupe les filtres de la page.
        html.Section(
            style={**STYLE_CARTE, "marginBottom": "24px"},
            children=[
                html.H2(
                    "Explorer les opérations",
                    style={"fontSize": "18px", "marginTop": "0"},
                ),
                html.Div(
                    style={
                        "display": "grid",
                        "gridTemplateColumns": "repeat(3, minmax(0, 1fr))",
                        "gap": "20px",
                    },
                    children=[
                        # Filtre de période.
                        html.Div([
                            html.Label("Période"),
                            dcc.Dropdown(
                                options=[
                                    {"label": "2005–2025", "value": "2005-2025"}
                                ],
                                value="2005-2025",
                                clearable=False,
                            ),
                        ]),

                        # Filtre de zone maritime.
                        html.Div([
                            html.Label("Zone maritime"),
                            dcc.Dropdown(
                                options=[
                                    {"label": "Toutes les zones", "value": "toutes"}
                                ],
                                value="toutes",
                                clearable=False,
                            ),
                        ]),

                        # Filtre de type d'événement.
                        html.Div([
                            html.Label("Type d’événement"),
                            dcc.Dropdown(
                                options=[
                                    {"label": "Tous les événements", "value": "tous"}
                                ],
                                value="tous",
                                clearable=False,
                            ),
                        ]),
                    ],
                ),
                html.P(
                    "Les filtres seront connectés aux données dans une prochaine étape.",
                    style={
                        "fontSize": "12px",
                        "color": COULEUR_TURQUOISE,
                        "marginBottom": "0",
                        "marginTop": "16px",
                    },
                ),
            ],
        ),

        # Affiche les trois indicateurs clés.
        html.Section(
            style={
                "display": "grid",
                "gridTemplateColumns": "repeat(3, minmax(0, 1fr))",
                "gap": "20px",
                "marginBottom": "28px",
            },
            children=[
                creer_carte_kpi(
                    "Opérations recensées",
                    "—",
                    "Nombre total d'opérations",
                    COULEUR_ORANGE,
                ),
                creer_carte_kpi(
                    "Personnes secourues",
                    "—",
                    "Bilan des opérations de secours",
                    COULEUR_TURQUOISE,
                ),
                creer_carte_kpi(
                    "Durée médiane",
                    "—",
                    "Temps entre l'alerte et la fin",
                    COULEUR_ORANGE,
                ),
            ],
        ),

        # Affiche la carte de densité provisoire.
        html.Section(
            style={**STYLE_CARTE, "marginBottom": "28px"},
            children=[
                html.H2(
                    "Répartition géographique des opérations",
                    style={"fontSize": "20px", "marginTop": "0"},
                ),
                html.P(
                    "Concentration des opérations disposant de coordonnées.",
                    style={"color": COULEUR_SECONDAIRE, "fontSize": "14px"},
                ),
                dcc.Graph(
                    figure=creer_carte_densite(),
                    config={"displayModeBar": False},
                ),
            ],
        ),

        # Place les graphiques annuels et événementiels côte à côte.
        html.Section(
            style={
                "display": "grid",
                "gridTemplateColumns": "repeat(2, minmax(0, 1fr))",
                "gap": "24px",
                "marginBottom": "28px",
            },
            children=[
                # Montre l'évolution annuelle des opérations.
                html.Div(
                    style=STYLE_CARTE,
                    children=[
                        html.H2(
                            "Évolution annuelle",
                            style={"fontSize": "18px", "marginTop": "0"},
                        ),
                        dcc.Graph(
                            figure=creer_graphique_annuel(),
                            config={"displayModeBar": False},
                        ),
                    ],
                ),

                # Montre les catégories d'événements les plus fréquentes.
                html.Div(
                    style=STYLE_CARTE,
                    children=[
                        html.H2(
                            "Types d'événements",
                            style={"fontSize": "18px", "marginTop": "0"},
                        ),
                        dcc.Graph(
                            figure=creer_graphique_evenements(),
                            config={"displayModeBar": False},
                        ),
                    ],
                ),
            ],
        ),

        # Regroupe les conditions maritimes et les durées d'opération.
        html.Section(
            style={
                "display": "grid",
                "gridTemplateColumns": "repeat(2, minmax(0, 1fr))",
                "gap": "24px",
                "marginBottom": "28px",
            },
            children=[
                # Compare les niveaux de vent et l'état de la mer.
                html.Div(
                    style=STYLE_CARTE,
                    children=[
                        html.H2(
                            "Conditions maritimes",
                            style={"fontSize": "18px", "marginTop": "0"},
                        ),
                        dcc.Graph(
                            figure=creer_graphique_conditions(),
                            config={"displayModeBar": False},
                        ),
                    ],
                ),

                # Montre les durées comprises entre 0 et 24 heures.
                html.Div(
                    style=STYLE_CARTE,
                    children=[
                        html.H2(
                            "Durée des opérations",
                            style={"fontSize": "18px", "marginTop": "0"},
                        ),
                        dcc.Graph(
                            figure=creer_graphique_durees(),
                            config={"displayModeBar": False},
                        ),
                        html.P(
                            "Les durées négatives et supérieures à 24 h sont exclues de cet histogramme provisoire.",
                            style={
                                "fontSize": "12px",
                                "color": COULEUR_SECONDAIRE,
                            },
                        ),
                    ],
                ),
            ],
        ),
    ],
)


# Lance le serveur local pour afficher le tableau de bord.
if __name__ == "__main__":
    app.run(debug=True)
