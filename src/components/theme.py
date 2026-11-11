"""Charte graphique « Signalétique portuaire » : couleurs des figures Plotly.

Les couleurs de la page (fond, cartes, typographie) sont dans
`assets/style.css` ; ce fichier ne contient que ce que Plotly doit connaître.
Changer de charte = remplacer ce fichier et `assets/style.css`.
"""

from typing import Any

# --- Couleurs de base ----------------------------------------------------------
COULEUR_PRINCIPALE = "#1F4E79"
COULEUR_ACCENT = "#B5442F"
COULEUR_TEXTE = "#1E2A33"
COULEUR_SECONDAIRE = "#5E6B76"
COULEUR_BORDURE = "#DDE3E8"
COULEUR_FOND = "#FFFFFF"
POLICE = "'Public Sans', 'Segoe UI', Arial, sans-serif"
# Police des titres de graphiques : la même que les titres de la page.
POLICE_TITRE = "'Barlow Condensed', 'Arial Narrow', sans-serif"
COULEUR_TITRE = "#163A5C"
COULEUR_GRILLE = "#EDF1F4"

# Couleur des séries uniques (barres, boîtes, histogramme).
COULEUR_SERIE = "#1F4E79"
COULEUR_SERIE_CLAIRE = "rgba(31, 78, 121, 0.22)"

# Couleur fixe par famille : une famille garde la même couleur partout.
COULEURS_FAMILLES = {
    "Avarie ou panne": "#E3B23C",
    "Accident de navire": "#B5442F",
    "Difficulté de navigation": "#7BA7C7",
    "Personne à la mer ou disparue": "#7A1F1F",
    "Baignade et loisirs": "#3C7A5A",
    "Médical": "#5B4B8A",
    "Fausse alerte ou situation indéterminée": "#9AA5B1",
    "Sûreté et migrations": "#1F4E79",
    "Autre": "#C5CCD3",
    "Non renseigné": "#E6EAEE",
}

# Du moins grave au plus grave.
COULEURS_GRAVITE = {
    "Aucun blessé, décès ou disparu": "#E6EBEF",
    "Blessés": "#E3B23C",
    "Décès ou disparus": "#B5442F",
}

# Échelle continue des cartes de chaleur (pourcentages).
ECHELLE_CHALEUR = [[0.0, "#FFFFFF"], [0.5, "#8FB3D1"], [1.0, "#1F4E79"]]

# Fond de carte (tuiles libres, sans clé d'accès).
STYLE_FOND_CARTE = "carto-positron"

# --- Mise en page commune des figures Plotly -------------------------------------
_AXE: dict[str, Any] = {
    "gridcolor": COULEUR_GRILLE,
    "zerolinecolor": COULEUR_BORDURE,
    "linecolor": COULEUR_BORDURE,
    "tickfont": {"size": 12, "color": COULEUR_SECONDAIRE},
    "title": {"font": {"size": 12.5, "color": COULEUR_SECONDAIRE}, "standoff": 12},
}

LAYOUT_GRAPHIQUE: dict[str, Any] = {
    "height": 380,
    "margin": {"l": 10, "r": 10, "t": 78, "b": 10},
    "paper_bgcolor": COULEUR_FOND,
    "plot_bgcolor": COULEUR_FOND,
    "font": {"family": POLICE, "color": COULEUR_TEXTE, "size": 13},
    "title": {
        "x": 0, "xanchor": "left", "y": 0.98, "yanchor": "top", "yref": "container",
        "font": {"family": POLICE_TITRE, "size": 21, "color": COULEUR_TITRE},
        "subtitle": {"font": {"size": 12.5, "color": COULEUR_SECONDAIRE}},
    },
    "legend": {"title": {"text": ""}, "bgcolor": "rgba(0,0,0,0)",
               "font": {"size": 12, "color": COULEUR_TEXTE}},
    "hoverlabel": {"font": {"family": POLICE}},
    "xaxis": _AXE,
    "yaxis": _AXE,
    # Format français : virgule décimale, espace pour les milliers.
    "separators": ", ",
}
