"""Registre des onglets d'analyse et des graphiques qu'ils contiennent.

Pour ajouter un graphique : écrire une fonction `figure_...(donnees)` dans un
module `src/components/figures_*.py`, puis l'ajouter à la liste de l'onglet
voulu ci-dessous. Pour ajouter un onglet : ajouter une entrée à `ONGLETS`.
"""

from collections.abc import Callable
from dataclasses import dataclass, field

import pandas as pd
import plotly.graph_objects as go

from src.components import figures_conditions as conditions
from src.components import figures_consequences as consequences
from src.components import figures_duree as duree
from src.components import figures_ou as ou
from src.components import figures_quand as quand
from src.utils.messages import (
    FonctionMessages,
    messages_conditions,
    messages_consequences,
    messages_duree,
    messages_ou,
    messages_quand,
)

FonctionFigure = Callable[[pd.DataFrame], go.Figure]


@dataclass(frozen=True)
class Graphique:
    """Un graphique de l'onglet : sa fonction, sa largeur et une note de lecture."""

    fonction: FonctionFigure
    pleine_largeur: bool = False
    note: str = ""


@dataclass(frozen=True)
class Onglet:
    """Un onglet d'analyse : question posée, messages à retenir, graphiques."""

    identifiant: str
    titre: str
    question: str
    graphiques: list[Graphique] = field(default_factory=list)
    messages: FonctionMessages | None = None


NOTE_FAMILLES = (
    "Les familles regroupent les 68 types d'événements détaillés : elles restent "
    "comparables malgré le changement de logiciel de saisie en 2019-2021."
)
NOTE_OBSERVATION = (
    "Ces chiffres décrivent les opérations déclenchées, pas le risque d'accident : "
    "il y a davantage de monde en mer par beau temps et en été."
)

ONGLETS: list[Onglet] = [
    Onglet(
        "quand",
        "Quand ?",
        "À quels moments de l'année chaque type d'événement est-il le plus fréquent ?",
        graphiques=[
            Graphique(quand.figure_mois_famille, pleine_largeur=True),
            Graphique(quand.figure_saison_famille),
            Graphique(quand.figure_saison_zone),
        ],
        messages=messages_quand,
    ),
    Onglet(
        "conditions",
        "Conditions",
        "Quelles conditions de vent et de mer accompagnent chaque type d'événement ?",
        graphiques=[
            Graphique(conditions.figure_vent_famille, note=NOTE_FAMILLES),
            Graphique(conditions.figure_mer_famille, note=NOTE_OBSERVATION),
            Graphique(
                conditions.figure_meteo_gravite, pleine_largeur=True,
                note="Vent et mer ne sont renseignés que pour environ 70 % des opérations.",
            ),
        ],
        messages=messages_conditions,
    ),
    Onglet(
        "consequences",
        "Conséquences",
        "Quels types d'événements ont les conséquences humaines les plus lourdes ?",
        graphiques=[
            Graphique(consequences.figure_famille_deces),
            Graphique(consequences.figure_famille_blesses),
            Graphique(consequences.figure_famille_impliques),
            Graphique(consequences.figure_evacuations),
        ],
        messages=messages_consequences,
    ),
    Onglet(
        "duree",
        "Durée et distance",
        "Quelles opérations durent le plus longtemps, et à quelle distance de la côte ?",
        graphiques=[
            Graphique(duree.figure_duree_vent),
            Graphique(duree.figure_duree_mer),
            Graphique(duree.figure_duree_famille),
            Graphique(
                duree.figure_distance_cote,
                note="Distance fournie par l'administration, fiable en métropole uniquement.",
            ),
            Graphique(duree.figure_gravite_distance, pleine_largeur=True),
        ],
        messages=messages_duree,
    ),
    Onglet(
        "ou",
        "Où ?",
        "Quels profils de risque distinguent les territoires ?",
        graphiques=[
            Graphique(ou.figure_cross_famille, pleine_largeur=True),
            Graphique(
                ou.figure_departement_famille, pleine_largeur=True,
                note="Le département n'est pas renseigné pour les opérations au large.",
            ),
            Graphique(ou.figure_zone_gravite, pleine_largeur=True),
        ],
        messages=messages_ou,
    ),
    Onglet(
        "evolution",
        "Évolution",
        "Comment les opérations ont-elles évolué depuis 1985 ?",
    ),
]

ONGLETS_PAR_IDENTIFIANT = {onglet.identifiant: onglet for onglet in ONGLETS}
