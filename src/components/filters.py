"""Panneau de filtres : période, mois, CROSS, famille d'événements, périmètre."""

from dash import dcc, html

from config import (
    ANNEE_DEBUT_DEFAUT,
    ANNEE_FIN_DEFAUT,
    ANNEE_MAX,
    ANNEE_MIN,
    MOIS_DEBUT_DEFAUT,
    MOIS_FIN_DEFAUT,
    NOMS_MOIS,
    VALEUR_TOUTES,
)
from src.utils.queries import (
    PERIMETRE_METROPOLE,
    PERIMETRE_OUTRE_MER,
    PERIMETRE_TOUT,
)


def _options_dropdown(valeurs: list[str], libelle_tout: str) -> list[dict[str, str]]:
    """Prépare les options d'une liste déroulante avec un choix « tout »."""
    options = [{"label": libelle_tout, "value": VALEUR_TOUTES}]
    options.extend({"label": valeur, "value": valeur} for valeur in valeurs)
    return options


def _bloc_filtre(
    libelle: str, *controles: dcc.Dropdown | dcc.RangeSlider | dcc.RadioItems | html.Label
) -> html.Div:
    """Associe un libellé à un ou plusieurs contrôles de filtre."""
    return html.Div(
        className="bloc-filtre",
        children=[html.Label(libelle, className="libelle-filtre"), *controles],
    )


def creer_panneau_filtres(cross: list[str], familles: list[str]) -> html.Section:
    """Construit le panneau des filtres communs à toute la page."""
    curseur_periode = dcc.RangeSlider(
        id="filtre-periode",
        min=ANNEE_MIN,
        max=ANNEE_MAX,
        step=1,
        value=[ANNEE_DEBUT_DEFAUT, ANNEE_FIN_DEFAUT],
        marks={annee: str(annee) for annee in range(ANNEE_MIN, ANNEE_MAX + 1, 10)},
        allowCross=False,
        tooltip={"placement": "bottom"},
    )
    # Mois de l'année, pour se concentrer sur une saison (ex. juin à août pour l'été).
    curseur_mois = dcc.RangeSlider(
        id="filtre-mois",
        min=1,
        max=12,
        step=1,
        value=[MOIS_DEBUT_DEFAUT, MOIS_FIN_DEFAUT],
        marks={mois: NOMS_MOIS[mois] for mois in range(1, 13)},
        allowCross=True,
        # Pas de cases de saisie : « 6 » ou « 8 » se lisent mal, les noms des mois suffisent.
        allow_direct_input=False,
    )
    liste_cross = dcc.Dropdown(
        id="filtre-cross",
        options=_options_dropdown(cross, "Tous les CROSS"),
        value=VALEUR_TOUTES,
        clearable=False,
    )
    liste_familles = dcc.Dropdown(
        id="filtre-famille",
        options=_options_dropdown(familles, "Toutes les familles"),
        value=VALEUR_TOUTES,
        clearable=False,
    )
    choix_perimetre = dcc.RadioItems(
        id="filtre-perimetre",
        options=[
            {"label": "Tout", "value": PERIMETRE_TOUT},
            {"label": "Métropole", "value": PERIMETRE_METROPOLE},
            {"label": "Outre-mer", "value": PERIMETRE_OUTRE_MER},
        ],
        value=PERIMETRE_TOUT,
        inline=True,
        inputStyle={"marginRight": "4px", "marginLeft": "10px"},
    )
    return html.Section(
        className="panneau panneau-filtres",
        children=[
            html.H2("Explorer les opérations", className="titre-section"),
            html.Div(
                className="grille-filtres",
                children=[
                    _bloc_filtre(
                        "Période (années)",
                        curseur_periode,
                        html.Label("Mois de l'année", className="libelle-filtre libelle-mois"),
                        curseur_mois,
                    ),
                    _bloc_filtre("CROSS", liste_cross),
                    _bloc_filtre("Famille d'événements", liste_familles),
                    _bloc_filtre("Périmètre", choix_perimetre),
                ],
            ),
            html.P(
                "Tous les indicateurs et graphiques suivent ces filtres.",
                className="legende",
            ),
        ],
    )
