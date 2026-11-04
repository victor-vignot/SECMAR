"""Page principale du tableau de bord SECMAR."""

from dash import Dash, Input, Output, html

from src.components.carte import creer_carte, creer_section_carte, decrire_positions
from src.components.filters import creer_panneau_filtres
from src.components.kpi import creer_carte_kpi, formater_duree, formater_nombre
from src.utils.queries import (
    Filtres,
    calculer_kpi,
    charger_operations,
    charger_options_filtres,
)

# Entrées communes à tous les callbacks : les quatre filtres.
ENTREES_FILTRES = [
    Input("filtre-periode", "value"),
    Input("filtre-cross", "value"),
    Input("filtre-famille", "value"),
    Input("filtre-perimetre", "value"),
]


def lire_filtres(periode: list[int], cross: str, famille: str, perimetre: str) -> Filtres:
    """Convertit les valeurs des composants Dash en objet `Filtres`."""
    annee_debut, annee_fin = periode
    return Filtres(int(annee_debut), int(annee_fin), cross, famille, perimetre)


def creer_entete() -> html.Header:
    """Construit l'en-tête de la page."""
    return html.Header(
        className="entete",
        children=[
            html.Img(src="/assets/logo.svg", alt="", className="entete-logo"),
            html.Div(
                className="entete-textes",
                children=[
                    html.H1("SECMAR"),
                    html.P(
                        "Observatoire des opérations de secours en mer "
                        "coordonnées par les CROSS"
                    ),
                ],
            ),
        ],
    )


def creer_section_kpi() -> html.Section:
    """Construit la rangée des cinq indicateurs clés."""
    return html.Section(
        className="grille-kpi",
        children=[
            creer_carte_kpi("Opérations", "kpi-operations",
                            "Opérations coordonnées sur la sélection", "principal"),
            creer_carte_kpi("Personnes secourues", "kpi-secourues",
                            "Total déclaré", "secondaire"),
            creer_carte_kpi("Personnes blessées", "kpi-blessees",
                            "Total déclaré", "alerte"),
            creer_carte_kpi("Personnes décédées", "kpi-decedees",
                            "Total déclaré", "grave"),
            creer_carte_kpi("Durée médiane", "kpi-duree",
                            "Opérations de moins de 72 h", "secondaire"),
        ],
    )


def creer_page_dashboard() -> html.Div:
    """Construit la page complète (appelée une fois au lancement)."""
    cross, familles = charger_options_filtres()
    # Préchargement de la vue par défaut : le premier affichage est immédiat.
    charger_operations(Filtres())
    return html.Div(
        className="page",
        children=[
            creer_entete(),
            creer_panneau_filtres(cross, familles),
            creer_section_kpi(),
            creer_section_carte(),
        ],
    )


def enregistrer_callbacks(app: Dash) -> None:
    """Déclare les interactions entre les filtres, les KPI et la carte."""

    @app.callback(
        Output("kpi-operations", "children"),
        Output("kpi-secourues", "children"),
        Output("kpi-blessees", "children"),
        Output("kpi-decedees", "children"),
        Output("kpi-duree", "children"),
        Output("graphique-carte", "figure"),
        Output("note-carte", "children"),
        *ENTREES_FILTRES,
    )
    def mettre_a_jour_vue_generale(periode, cross, famille, perimetre):  # type: ignore[no-untyped-def]
        donnees = charger_operations(lire_filtres(periode, cross, famille, perimetre))
        kpi = calculer_kpi(donnees)
        return (
            formater_nombre(kpi["operations"]),
            formater_nombre(kpi["secourues"]),
            formater_nombre(kpi["blessees"]),
            formater_nombre(kpi["decedees"]),
            formater_duree(kpi["duree_mediane"]),
            creer_carte(donnees),
            decrire_positions(donnees),
        )
