"""Page principale du tableau de bord SECMAR."""

import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input, Output, dcc, html

from src.components.carte import creer_carte, creer_section_carte, decrire_positions
from src.components.filters import creer_panneau_filtres
from src.components.kpi import creer_carte_kpi, formater_duree, formater_nombre
from src.components.messages import creer_bandeau_messages
from src.components.theme import COULEUR_PRINCIPALE
from src.pages.onglets import ONGLETS, ONGLETS_PAR_IDENTIFIANT, Graphique, Onglet
from src.utils.familles import FAMILLE_INCONNUE
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


def creer_section_analyses() -> html.Section:
    """Construit les onglets d'analyse ; leur contenu est rempli par callback."""
    return html.Section(
        className="panneau panneau-analyses",
        children=[
            html.H2("Analyses", className="titre-section"),
            dcc.Tabs(
                id="onglets",
                value=ONGLETS[0].identifiant,
                className="onglets",
                children=[
                    dcc.Tab(label=onglet.titre, value=onglet.identifiant,
                            className="onglet", selected_className="onglet-actif")
                    for onglet in ONGLETS
                ],
            ),
            dcc.Loading(
                type="circle",
                color=COULEUR_PRINCIPALE,
                children=html.Div(id="contenu-onglet", className="contenu-onglet"),
            ),
        ],
    )


def creer_pied_page() -> html.Footer:
    """Construit le pied de page avec la source des données."""
    return html.Footer(
        className="pied-page",
        children=[
            "Source : ",
            html.A(
                "Opérations coordonnées par les CROSS (data.gouv.fr, Licence Ouverte)",
                href="https://www.data.gouv.fr/fr/datasets/operations-coordonnees-par-les-cross/",
                target="_blank",
            ),
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
            creer_section_analyses(),
            creer_pied_page(),
        ],
    )


def construire_bloc_graphique(graphique: Graphique, donnees: pd.DataFrame) -> html.Div:
    """Assemble un graphique et sa note de lecture."""
    classe = "bloc-graphique pleine-largeur" if graphique.pleine_largeur else "bloc-graphique"
    enfants: list[dcc.Graph | html.P] = [
        dcc.Graph(figure=graphique.fonction(donnees), config={"displaylogo": False})
    ]
    if graphique.note:
        enfants.append(html.P(graphique.note, className="note-lecture"))
    return html.Div(className=classe, children=enfants)


def construire_onglet(onglet: Onglet, donnees: pd.DataFrame) -> list[html.P | html.Div]:
    """Construit le contenu d'un onglet : question, messages à retenir, graphiques.

    Les opérations sans type d'événement (« Non renseigné ») restent dans les
    indicateurs, mais pas dans les analyses : elles n'apprennent rien.
    """
    non_renseignees = int((donnees["famille"] == FAMILLE_INCONNUE).sum())
    donnees = donnees[donnees["famille"] != FAMILLE_INCONNUE]
    if isinstance(donnees["famille"].dtype, pd.CategoricalDtype):
        # La catégorie vide disparaîtrait sinon des données mais pas des graphiques.
        donnees = donnees.assign(famille=donnees["famille"].cat.remove_unused_categories())
    contenu: list[html.P | html.Div] = [html.P(onglet.question, className="question-onglet")]
    if onglet.messages is not None:
        bandeau = creer_bandeau_messages(onglet.messages(donnees))
        if bandeau is not None:
            contenu.append(bandeau)
    if not onglet.graphiques:
        contenu.append(html.P("Les graphiques de cet onglet sont en préparation.",
                              className="note-lecture"))
        return contenu
    contenu.append(
        html.Div(
            className="grille-graphiques",
            children=[construire_bloc_graphique(g, donnees) for g in onglet.graphiques],
        )
    )
    if non_renseignees:
        contenu.append(html.P(
            f"{formater_nombre(non_renseignees)} opérations sans type d'événement renseigné "
            "comptent dans les indicateurs mais ne figurent pas dans ces analyses.",
            className="note-lecture note-onglet"))
    return contenu


def enregistrer_callbacks(app: Dash) -> None:
    """Déclare les interactions entre les filtres, les KPI, la carte et les onglets."""

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
    def mettre_a_jour_vue_generale(
        periode: list[int], cross: str, famille: str, perimetre: str
    ) -> tuple[str, str, str, str, str, go.Figure, str]:
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

    @app.callback(
        Output("contenu-onglet", "children"),
        Input("onglets", "value"),
        *ENTREES_FILTRES,
    )
    def afficher_onglet(
        identifiant: str, periode: list[int], cross: str, famille: str, perimetre: str
    ) -> list[html.P | html.Div]:
        # Seul l'onglet visible est calculé : la page reste fluide.
        donnees = charger_operations(lire_filtres(periode, cross, famille, perimetre))
        onglet = ONGLETS_PAR_IDENTIFIANT.get(identifiant, ONGLETS[0])
        return construire_onglet(onglet, donnees)
