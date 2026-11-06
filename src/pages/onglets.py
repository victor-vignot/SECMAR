"""Registre des onglets d'analyse et des graphiques qu'ils contiennent.

Pour ajouter un graphique : écrire une fonction `figure_...(donnees)` dans un
module `src/components/figures_*.py`, puis l'ajouter à la liste de l'onglet
voulu ci-dessous. Pour ajouter un onglet : ajouter une entrée à `ONGLETS`.
"""

from collections.abc import Callable
from dataclasses import dataclass, field

import pandas as pd
import plotly.graph_objects as go

from src.utils.messages import FonctionMessages

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


ONGLETS: list[Onglet] = [
    Onglet(
        "quand",
        "Quand ?",
        "À quels moments de l'année chaque type d'événement est-il le plus fréquent ?",
    ),
    Onglet(
        "conditions",
        "Conditions",
        "Quelles conditions de vent et de mer accompagnent chaque type d'événement ?",
    ),
    Onglet(
        "consequences",
        "Conséquences",
        "Quels types d'événements ont les conséquences humaines les plus lourdes ?",
    ),
    Onglet(
        "duree",
        "Durée et distance",
        "Quelles opérations durent le plus longtemps, et à quelle distance de la côte ?",
    ),
    Onglet(
        "ou",
        "Où ?",
        "Quels profils de risque distinguent les territoires ?",
    ),
    Onglet(
        "evolution",
        "Évolution",
        "Comment les opérations ont-elles évolué depuis 1985 ?",
    ),
]

ONGLETS_PAR_IDENTIFIANT = {onglet.identifiant: onglet for onglet in ONGLETS}
