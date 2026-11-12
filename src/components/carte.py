"""Carte géographique des opérations (représentation géolocalisée)."""

import math

import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html

from config import MAX_POINTS_CARTE, NOMS_MOIS_LONGS
from src.components.theme import COULEURS_FAMILLES, LAYOUT_GRAPHIQUE, STYLE_FOND_CARTE
from src.utils.familles import FAMILLE_INCONNUE, ORDRE_FAMILLES

# Deux façons de colorer les points, au choix de l'utilisateur.
MODE_FAMILLE = "famille"
MODE_EVENEMENT = "evenement"
OPTIONS_MODE = [
    {"label": "Par famille d'événements", "value": MODE_FAMILLE},
    {"label": "Par type d'événement précis", "value": MODE_EVENEMENT},
]

# Mode « type précis » : les types les plus fréquents de la sélection, les autres regroupés.
NOMBRE_TYPES_CARTE = 8
AUTRES_TYPES = "Autres types"
COULEURS_TYPES = [
    "#1F4E79", "#E3B23C", "#B5442F", "#3C7A5A",
    "#5B4B8A", "#7BA7C7", "#C9772B", "#7A1F1F",
]
COULEUR_AUTRES_TYPES = "#C5CCD3"

# Cadrage : la carte s'ajuste sur le cœur de la sélection (on ignore 20 % de points excentrés).
QUANTILES_CADRAGE = (0.1, 0.9)
PART_METROPOLE_CADRAGE = 0.5
DISTANCE_LOINTAINE_MN = 200
CENTRE_PAR_DEFAUT = {"lat": 46.5, "lon": 2.5}
ZOOM_PAR_DEFAUT = 4.6
ZOOM_MAXIMAL = 9.0

# Infobulle d'une opération, à partir des colonnes de `customdata`.
INFOBULLE = (
    "<b>%{customdata[0]}</b><br>"
    "Famille : %{customdata[1]}<br>"
    "CROSS : %{customdata[2]} · %{customdata[3]}<br>"
    "Personnes impliquées : %{customdata[4]} · secourues : %{customdata[5]}<br>"
    "Blessées : %{customdata[6]} · décédées ou disparues : %{customdata[7]}<br>"
    "Distance de la côte : %{customdata[8]} · durée : %{customdata[9]}"
    "<extra></extra>"
)


def positions_valides(donnees: pd.DataFrame) -> pd.DataFrame:
    """Opérations dont la position peut être dessinée."""
    points = donnees.dropna(subset=["latitude", "longitude"])
    points = points[
        points["latitude"].between(-90, 90)
        & points["longitude"].between(-180, 180)
        # Les positions (0, 0) sont des valeurs par défaut, pas des lieux réels.
        & ~(points["latitude"].eq(0) & points["longitude"].eq(0))
        # Sans type d'événement, un point n'apprend rien : il n'est pas dessiné.
        & points["famille"].ne(FAMILLE_INCONNUE)
    ]
    return points


def preparer_points_carte(donnees: pd.DataFrame) -> pd.DataFrame:
    """Positions valides, limitées en nombre pour garder une carte fluide."""
    points = positions_valides(donnees)
    if len(points) > MAX_POINTS_CARTE:
        # Échantillon reproductible pour garder une carte fluide.
        points = points.sample(n=MAX_POINTS_CARTE, random_state=42)
    return points


def decrire_positions(donnees: pd.DataFrame) -> str:
    """Phrase indiquant combien d'opérations ne figurent pas sur la carte."""
    sans_position = int(donnees["latitude"].isna().sum())
    if sans_position == 0:
        return "Toutes les opérations de la sélection ont une position."
    part = sans_position / len(donnees) * 100
    nombre = f"{sans_position:,}".replace(",", " ")
    return (
        f"{nombre} opérations de la sélection ({part:.0f} %) n'ont pas de position "
        "fiable (position absente, à (0, 0) ou à plus de 5 km dans les terres) : "
        "elles comptent dans les indicateurs mais pas sur la carte."
    )


def _texte_nombre(serie: pd.Series) -> pd.Series:
    return serie.map(lambda v: "?" if pd.isna(v) else f"{int(v)}")


def _texte_distance(serie: pd.Series) -> pd.Series:
    return serie.map(lambda v: "non connue" if pd.isna(v) else f"{v:.1f} milles".replace(".", ","))


def _texte_duree(serie: pd.Series) -> pd.Series:
    def formater(heures: float) -> str:
        if pd.isna(heures):
            return "non connue"
        nombre_heures, minutes = divmod(round(heures * 60), 60)
        return f"{nombre_heures} h {minutes:02d}" if nombre_heures else f"{minutes} min"

    return serie.map(formater)


def details_operations(points: pd.DataFrame) -> pd.DataFrame:
    """Colonnes de texte affichées dans l'infobulle de chaque opération."""
    decedes = points["personnes_decedees"].fillna(0) + points["personnes_disparues"].fillna(0)
    periode = points["mois"].map(NOMS_MOIS_LONGS).fillna("") + " " + points["annee"].astype(str)
    return pd.DataFrame({
        "evenement": points["evenement"].fillna("Type non renseigné"),
        "famille": points["famille"].astype(str),
        "cross": points["cross"].fillna("?"),
        "periode": periode.str.strip().str.capitalize(),
        "impliquees": _texte_nombre(points["personnes_impliquees"]),
        "secourues": _texte_nombre(points["personnes_secourues"]),
        "blessees": _texte_nombre(points["personnes_blessees"]),
        "decedees": _texte_nombre(decedes),
        "distance": _texte_distance(points["distance_cote_mn"]),
        "duree": _texte_duree(points["duree_heures"]),
    })


def cadrage(points: pd.DataFrame) -> tuple[dict[str, float], float]:
    """Centre et zoom qui encadrent le cœur des points de la sélection."""
    if points.empty:
        return CENTRE_PAR_DEFAUT, ZOOM_PAR_DEFAUT
    # Les opérations lointaines (relais d'alertes à l'étranger) ne guident pas le cadrage.
    proches = points[~(points["distance_cote_mn"] > DISTANCE_LOINTAINE_MN)]
    points = proches if not proches.empty else points
    metropole = points[points["est_metropolitain"].astype(bool)]
    if len(metropole) >= PART_METROPOLE_CADRAGE * len(points):
        # Sélection surtout métropolitaine : on cadre la métropole, l'outre-mer reste
        # accessible en dézoomant (ou avec le filtre « Outre-mer »).
        points = metropole
    bas, haut = QUANTILES_CADRAGE
    lat_min, lat_max = points["latitude"].quantile([bas, haut])
    lon_min, lon_max = points["longitude"].quantile([bas, haut])
    # Centre médian : il reste sur le cœur de l'activité même si des points sont dispersés.
    centre = {"lat": float(points["latitude"].median()), "lon": float(points["longitude"].median())}
    # Un niveau de zoom divise par deux l'étendue affichée (≈ 360° au zoom 0).
    etendue = max(lon_max - lon_min, (lat_max - lat_min) * 1.6, 0.05)
    zoom = min(math.log2(360 / etendue) - 0.6, ZOOM_MAXIMAL)
    return centre, round(zoom, 2)


def _categories(points: pd.DataFrame, mode: str) -> tuple[pd.Series, list[str], dict[str, str]]:
    """Catégorie de chaque point, ordre de la légende et couleurs."""
    if mode == MODE_EVENEMENT:
        frequents = points["evenement"].value_counts().index[:NOMBRE_TYPES_CARTE].tolist()
        categorie = points["evenement"].where(points["evenement"].isin(frequents), AUTRES_TYPES)
        couleurs = dict(zip(frequents, COULEURS_TYPES, strict=False))
        couleurs[AUTRES_TYPES] = COULEUR_AUTRES_TYPES
        return categorie, [*frequents, AUTRES_TYPES], couleurs
    familles = [f for f in ORDRE_FAMILLES if f != FAMILLE_INCONNUE]
    return points["famille"].astype(str), familles, COULEURS_FAMILLES


def creer_carte(donnees: pd.DataFrame, mode: str = MODE_FAMILLE) -> go.Figure:
    """Carte des opérations, colorées par famille ou par type d'événement précis."""
    valides = positions_valides(donnees)
    points = preparer_points_carte(donnees)
    categorie, ordre, couleurs = _categories(valides, mode)
    effectifs = categorie.value_counts()
    categorie = categorie.loc[points.index]
    details = details_operations(points)
    figure = go.Figure()
    for nom in ordre:
        masque = categorie == nom
        if not masque.any():
            continue
        figure.add_trace(
            go.Scattermap(
                lat=points.loc[masque, "latitude"],
                lon=points.loc[masque, "longitude"],
                mode="markers",
                # Effectif réel de la sélection, pas celui de l'échantillon dessiné.
                name=f"{nom} ({int(effectifs.get(nom, 0)):_})".replace("_", " "),
                marker={"size": 7, "opacity": 0.8, "color": couleurs.get(nom, "#9AA5B1")},
                customdata=details[masque].to_numpy(),
                hovertemplate=INFOBULLE,
            )
        )
    centre, zoom = cadrage(valides)
    figure.update_layout(
        height=600,
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        map={"style": STYLE_FOND_CARTE, "center": centre, "zoom": zoom},
        paper_bgcolor=LAYOUT_GRAPHIQUE["paper_bgcolor"],
        font=LAYOUT_GRAPHIQUE["font"],
        hoverlabel={"bgcolor": "#FFFFFF", "bordercolor": "#C9D2DA",
                    "font": {"size": 13, "color": "#1E2A33"}},
        legend={
            "orientation": "h", "x": 0, "y": -0.01, "yanchor": "top",
            "itemsizing": "constant", "font": {"size": 12},
        },
        # Le zoom choisi à la main est gardé tant que filtres et mode ne changent pas.
        uirevision=f"{mode}-{len(points)}",
    )
    return figure


def creer_section_carte() -> html.Section:
    """Construit la section contenant la carte et le choix de coloration."""
    return html.Section(
        className="panneau panneau-carte",
        children=[
            html.Div(
                className="entete-carte",
                children=[
                    html.H2("Où ont lieu les opérations ?", className="titre-section"),
                    dcc.RadioItems(
                        id="mode-carte",
                        options=OPTIONS_MODE,
                        value=MODE_FAMILLE,
                        className="bascule",
                    ),
                ],
            ),
            dcc.Graph(id="graphique-carte", config={"displayModeBar": False,
                                                     "scrollZoom": True}),
            html.P(id="note-carte", className="legende legende-forte"),
            html.P(
                "Survoler un point pour le détail de l'opération ; molette pour zoomer. "
                "En mode « type précis », choisir une famille dans les filtres détaille ses "
                "types d'événements. "
                f"Au plus {MAX_POINTS_CARTE:_} points tirés au hasard, pour garder la carte "
                "fluide. Cliquer sur un élément de la légende pour l'afficher ou le "
                "masquer.".replace("_", " "),
                className="legende",
            ),
        ],
    )
