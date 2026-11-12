"""Figures de l'onglet « Évolution » : les opérations de 1985 à aujourd'hui."""

import math

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from config import EFFECTIF_MINIMAL, RUPTURES_SAISIE
from src.components.graphiques import (
    TextesFigure,
    appliquer_charte,
    courbes,
    figure_vide,
)
from src.components.theme import COULEUR_SECONDAIRE, COULEURS_FAMILLES
from src.utils.aggregations import evolution_annuelle
from src.utils.familles import ORDRE_FAMILLES

# Durée d'affichage de chaque année pendant l'animation (millisecondes).
DUREE_IMAGE_MS = 700

# Graduations lisibles pour l'axe logarithmique du nombre d'opérations.
GRADUATIONS_LOG = [30, 100, 300, 1000, 3000, 10000]
# Prolongement de l'axe vertical des bulles sous zéro (décès pour 1 000 opérations).
MARGE_BASSE_BULLES = 30

MESSAGE_DEUX_ANNEES = "Choisissez au moins deux années pour voir une évolution"


def figure_courbe_annuelle(donnees: pd.DataFrame) -> go.Figure:
    """Nombre d'opérations par an, une courbe par famille, ruptures de saisie grisées."""
    titre = "Les opérations année après année, par famille d'événements"
    if donnees["annee"].nunique() < 2:
        return figure_vide(titre, MESSAGE_DEUX_ANNEES)
    evolution = evolution_annuelle(donnees)
    periodes = ", ".join(f"{debut}-{fin}" for debut, fin, _ in RUPTURES_SAISIE)
    textes = TextesFigure(
        titre,
        f"Nombre d'opérations par an · zones grisées ({periodes}) : changements dans "
        "la façon d'enregistrer les opérations, à prendre en compte dans les comparaisons",
        "Année",
        "Nombre d'opérations",
    )
    figure = courbes(evolution, ("annee", "operations", "famille"), COULEURS_FAMILLES, textes)
    annees = evolution["annee"]
    for debut, fin, _ in RUPTURES_SAISIE:
        if annees.min() <= fin and annees.max() >= debut:
            figure.add_vrect(
                x0=debut - 0.5, x1=fin + 0.5,
                fillcolor=COULEUR_SECONDAIRE, opacity=0.12, line_width=0,
            )
    return figure


def figure_bulles_animees(donnees: pd.DataFrame) -> go.Figure:
    """Bulles animées : chaque famille se déplace d'année en année.

    Abscisse = nombre d'opérations (échelle log), ordonnée = décès et disparus
    pour 1 000 opérations, taille = personnes impliquées. Les familles de moins
    de 30 opérations dans l'année sont masquées (taux trop instable).
    """
    titre = "Volume et gravité des opérations, année après année"
    if donnees["annee"].nunique() < 2:
        return figure_vide(titre, MESSAGE_DEUX_ANNEES)
    evolution = evolution_annuelle(donnees)
    evolution = evolution[evolution["operations"] >= EFFECTIF_MINIMAL]
    if evolution["annee"].nunique() < 2:
        return figure_vide(titre, MESSAGE_DEUX_ANNEES)
    figure = px.scatter(
        _completer_annees(evolution, evolution["operations"].min() * 0.5),
        x="operations",
        y="taux_victimes",
        size="impliques",
        color="famille",
        animation_frame="annee",
        animation_group="famille",
        color_discrete_map=COULEURS_FAMILLES,
        category_orders={"famille": ORDRE_FAMILLES},
        log_x=True,
        size_max=48,
        range_x=[evolution["operations"].min() * 0.8, evolution["operations"].max() * 1.3],
        # Axe prolongé sous zéro : les bulles des familles peu meurtrières restent entières.
        range_y=[-MARGE_BASSE_BULLES, evolution["taux_victimes"].max() * 1.1],
        hover_name="famille",
        labels={
            "operations": "Nombre d'opérations dans l'année (échelle log)",
            "taux_victimes": "Décès et disparus pour 1 000 opérations",
            "impliques": "Personnes impliquées",
            "famille": "Famille d'événements",
            "annee": "Année",
        },
    )
    textes = TextesFigure(
        titre,
        "Une bulle par famille · taille : personnes impliquées · "
        "appuyez sur ▶ ou faites glisser le curseur des années",
        "Nombre d'opérations dans l'année (échelle log)",
        "Décès et disparus pour 1 000 opérations",
    )
    appliquer_charte(figure, textes)
    # Légende à taille fixe : une famille absente la première année garde sa pastille.
    figure.update_layout(height=560, legend={"title": {"text": ""}, "itemsizing": "constant"})
    # Taille minimale : les familles qui impliquent peu de personnes restent visibles.
    figure.update_traces(marker={"sizemin": 6})
    for image in figure.frames:
        for trace in image.data:
            trace.marker.sizemin = 6
    # Pas de graduation négative : le prolongement sous zéro ne sert qu'à l'affichage.
    figure.update_yaxes(tickvals=graduations_positives(evolution["taux_victimes"].max()))
    figure.update_xaxes(tickvals=GRADUATIONS_LOG, ticktext=[f"{v:,}".replace(",", " ")
                                                            for v in GRADUATIONS_LOG])
    # Animation plus lente que celle par défaut, pour suivre les bulles.
    lecture = figure.layout.updatemenus[0].buttons[0]
    lecture.args[1]["frame"]["duration"] = DUREE_IMAGE_MS
    lecture.args[1]["transition"]["duration"] = DUREE_IMAGE_MS // 2
    figure.layout.sliders[0].currentvalue.prefix = "Année : "
    return figure


def _completer_annees(evolution: pd.DataFrame, hors_champ: float) -> pd.DataFrame:
    """Une ligne par année et par famille, même vide.

    Plotly ne crée une série animée que pour les familles présentes la
    première année : sans cette grille complète, une famille apparue plus
    tard ne serait jamais dessinée. Une famille absente une année est placée
    à gauche du graphique (`hors_champ`), hors de la zone affichée : elle
    entre dans le champ l'année où elle apparaît et garde sa pastille de légende.
    """
    grille = pd.MultiIndex.from_product(
        [sorted(evolution["annee"].unique()), sorted(evolution["famille"].unique())],
        names=["annee", "famille"],
    )
    complete = evolution.set_index(["annee", "famille"]).reindex(grille).reset_index()
    complete["operations"] = complete["operations"].fillna(hors_champ)
    complete["taux_victimes"] = complete["taux_victimes"].fillna(0)
    # Une bulle de taille nulle n'est pas dessinée, même avec une taille minimale.
    complete["impliques"] = complete["impliques"].fillna(0).clip(lower=1)
    return complete


def graduations_positives(maximum: float) -> list[float]:
    """Graduations rondes de 0 au maximum (environ cinq), sans valeur négative."""
    pas_bruts = maximum / 5 if maximum > 0 else 1
    puissance = 10 ** math.floor(math.log10(pas_bruts))
    pas = next(m * puissance for m in (1, 2, 5, 10) if m * puissance >= pas_bruts)
    return [pas * i for i in range(int(maximum // pas) + 2)]
