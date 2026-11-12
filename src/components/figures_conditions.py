"""Figures de l'onglet « Conditions » : vent et état de la mer."""

import pandas as pd
import plotly.graph_objects as go

from config import GRAVITES
from src.components.graphiques import TextesFigure, carte_chaleur, formater_effectif
from src.components.theme import COULEUR_ACCENT
from src.utils.aggregations import profil_croise, taux_par_cases
from src.utils.messages import FAMILLE_MEDICALE

LIBELLES = {
    "classe_vent": "Force du vent (échelle de Beaufort)",
    "classe_mer": "État de la mer (échelle de Douglas)",
    "famille": "Famille d'événements",
}


def _profil_meteo_famille(donnees: pd.DataFrame, condition: str, titre: str) -> go.Figure:
    """Répartition des familles d'événements pour chaque classe météo."""
    tableau = profil_croise(donnees, condition, "famille")
    renseignees = int(tableau.totaux.sum())
    sous_titre = (
        f"Chaque colonne = 100 % des opérations de la classe · "
        f"{formater_effectif(renseignees)} opérations renseignées sur "
        f"{formater_effectif(len(donnees))}"
    )
    textes = TextesFigure(titre, sous_titre, LIBELLES[condition], LIBELLES["famille"])
    return carte_chaleur(tableau.pourcentages, tableau.effectifs, textes)


def figure_vent_famille(donnees: pd.DataFrame) -> go.Figure:
    """Force du vent × famille d'événements."""
    return _profil_meteo_famille(
        donnees, "classe_vent", "Quels événements selon la force du vent ?"
    )


def figure_mer_famille(donnees: pd.DataFrame) -> go.Figure:
    """État de la mer × famille d'événements."""
    figure = _profil_meteo_famille(
        donnees, "classe_mer", "Quels événements selon l'état de la mer ?"
    )
    familles = list(figure.data[0].y) if figure.data else []
    if FAMILLE_MEDICALE in familles:
        # Ligne encadrée : la part médicale augmente avec l'état de la mer.
        rang = familles.index(FAMILLE_MEDICALE)
        figure.add_shape(
            type="rect", x0=-0.5, x1=len(figure.data[0].x) - 0.5, y0=rang - 0.5, y1=rang + 0.5,
            line={"color": COULEUR_ACCENT, "width": 2.5},
        )
    return figure


def figure_meteo_gravite(donnees: pd.DataFrame) -> go.Figure:
    """Part des opérations avec victimes, pour chaque combinaison vent × mer."""
    avec_victimes = donnees["gravite"].ne(GRAVITES[0])
    taux, effectifs = taux_par_cases(donnees, "classe_mer", "classe_vent", avec_victimes)
    textes = TextesFigure(
        "Part des opérations avec blessés, décès ou disparus selon vent et mer",
        "Cases de moins de 30 opérations masquées",
        LIBELLES["classe_vent"],
        LIBELLES["classe_mer"],
    )
    return carte_chaleur(taux, effectifs, textes, libelle_valeur="Opérations avec victimes")
