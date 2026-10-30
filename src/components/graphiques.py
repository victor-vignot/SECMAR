"""Fonctions de création des graphiques du dashboard."""

import pandas as pd
import plotly.express as px

from src.components.theme import (
    COULEUR_ORANGE,
    COULEUR_TURQUOISE,
    LAYOUT_GRAPHIQUE,
)


# Affiche le nombre d'opérations par année.
def creer_graphique_annuel(donnees):
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
    figure.update_traces(
        line={"color": COULEUR_ORANGE, "width": 3},
        marker={"color": COULEUR_ORANGE, "size": 7},
    )
    figure.update_layout(**LAYOUT_GRAPHIQUE)
    figure.update_xaxes(dtick=2)
    return figure


# Affiche les catégories d'événements les plus fréquentes.
def creer_graphique_evenements(donnees):
    donnees = donnees.sort_values("nombre_operations").tail(8)

    figure = px.bar(
        donnees,
        x="nombre_operations",
        y="categorie_evenement",
        orientation="h",
        labels={
            "nombre_operations": "Nombre d'opérations",
            "categorie_evenement": "Catégorie d'événement",
        },
        color_discrete_sequence=[COULEUR_TURQUOISE],
    )
    figure.update_layout(**LAYOUT_GRAPHIQUE)
    return figure


# Affiche les événements détaillés les plus fréquents.
def creer_graphique_evenements_detailles(donnees):
    donnees = (
        donnees.groupby("evenement", as_index=False)
        ["nombre_operations"]
        .sum()
        .sort_values("nombre_operations")
        .tail(10)
    )

    figure = px.bar(
        donnees,
        x="nombre_operations",
        y="evenement",
        orientation="h",
        labels={
            "nombre_operations": "Nombre d'opérations",
            "evenement": "Événement détaillé",
        },
        color_discrete_sequence=[COULEUR_ORANGE],
    )
    figure.update_layout(**LAYOUT_GRAPHIQUE)
    return figure


# Compare les niveaux de vent et de mer.
def creer_graphique_conditions(donnees):
    vent = donnees[["vent_force"]].dropna().copy()
    vent["condition"] = "Force du vent"
    vent = vent.rename(columns={"vent_force": "niveau"})

    mer = donnees[["mer_force"]].dropna().copy()
    mer["condition"] = "État de la mer"
    mer = mer.rename(columns={"mer_force": "niveau"})

    combinees = pd.concat([vent, mer], ignore_index=True)
    combinees["niveau"] = pd.to_numeric(
        combinees["niveau"], errors="coerce"
    )
    combinees = combinees.dropna(subset=["niveau"])

    figure = px.histogram(
        combinees,
        x="niveau",
        color="condition",
        barmode="group",
        histfunc="count",
        labels={
            "niveau": "Niveau de force",
            "count": "Nombre d'opérations",
            "condition": "Condition maritime",
        },
        color_discrete_map={
            "Force du vent": COULEUR_ORANGE,
            "État de la mer": COULEUR_TURQUOISE,
        },
    )
    figure.update_layout(**LAYOUT_GRAPHIQUE)
    return figure


# Affiche la distribution des durées d'opération.
def creer_graphique_durees(donnees):
    durees = pd.to_numeric(
        donnees["duree_heures"], errors="coerce"
    ).dropna()

    # Garde provisoirement les durées comprises entre 0 et 24 heures.
    durees = durees[durees.between(0, 24)]

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
    figure.update_layout(**LAYOUT_GRAPHIQUE)
    return figure