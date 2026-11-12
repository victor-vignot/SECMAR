"""Constructeurs génériques de figures Plotly.

Chaque fonction reçoit un tableau déjà agrégé (voir `src/utils/aggregations.py`)
et applique la charte commune. Les figures de chaque onglet (modules
`figures_*.py`) s'appuient sur ces constructeurs.
"""

import textwrap
from dataclasses import dataclass

import pandas as pd
import plotly.graph_objects as go

from src.components.theme import (
    COULEUR_FOND,
    COULEUR_SECONDAIRE,
    COULEUR_SERIE,
    COULEUR_SERIE_CLAIRE,
    ECHELLE_CHALEUR,
    LAYOUT_GRAPHIQUE,
)

# Au-delà de cette longueur, le sous-titre passe sur deux lignes (sinon il est coupé).
LARGEUR_SOUS_TITRE = 85
# Longueur maximale d'une ligne de libellé sous une carte de chaleur.
LARGEUR_LIBELLE = 13

# Marge laissée après la plus grande valeur pour que son étiquette reste visible.
MARGE_ETIQUETTES = 1.18


@dataclass(frozen=True)
class TextesFigure:
    """Textes d'une figure : titre, sous-titre et libellés des axes."""

    titre: str
    sous_titre: str = ""
    libelle_x: str = ""
    libelle_y: str = ""


def appliquer_charte(figure: go.Figure, textes: TextesFigure) -> go.Figure:
    """Applique la mise en page commune, le titre et le sous-titre.

    Un sous-titre long est coupé en lignes, et la marge haute agrandie d'autant.
    """
    lignes = textwrap.wrap(textes.sous_titre, LARGEUR_SOUS_TITRE) or [""]
    figure.update_layout(**LAYOUT_GRAPHIQUE)
    figure.update_layout(
        title={"text": textes.titre, "subtitle": {"text": "<br>".join(lignes)}},
        margin={"t": LAYOUT_GRAPHIQUE["margin"]["t"] + 17 * (len(lignes) - 1)},
    )
    return figure


def figure_vide(titre: str, message: str = "Aucune opération pour ces filtres") -> go.Figure:
    """Figure affichée quand la sélection ne contient pas assez de données."""
    figure = go.Figure()
    figure.add_annotation(
        text=message, showarrow=False, font={"size": 14, "color": COULEUR_SECONDAIRE},
        xref="paper", yref="paper", x=0.5, y=0.5,
    )
    figure.update_xaxes(visible=False)
    figure.update_yaxes(visible=False)
    return appliquer_charte(figure, TextesFigure(titre))


def formater_effectif(nombre: float) -> str:
    """Formate un effectif avec une espace comme séparateur de milliers."""
    return f"{nombre:,.0f}".replace(",", " ")


def carte_chaleur(
    valeurs: pd.DataFrame,
    effectifs: pd.DataFrame,
    textes: TextesFigure,
    libelle_valeur: str = "% des opérations",
) -> go.Figure:
    """Carte de chaleur avec la valeur (en %) écrite dans chaque case."""
    if valeurs.empty or valeurs.isna().all().all():
        return figure_vide(textes.titre)
    texte = valeurs.map(lambda v: "" if pd.isna(v) else f"{v:.0f} %")
    figure = go.Figure(
        go.Heatmap(
            z=valeurs.to_numpy(dtype=float),
            x=[str(c) for c in valeurs.columns],
            y=[str(i) for i in valeurs.index],
            text=texte.to_numpy(),
            texttemplate="%{text}",
            customdata=effectifs.reindex_like(valeurs).to_numpy(dtype=float),
            colorscale=ECHELLE_CHALEUR,
            colorbar={"title": {"text": "%"}, "thickness": 12},
            hovertemplate=(
                f"{textes.libelle_x} : %{{x}}<br>{textes.libelle_y} : %{{y}}<br>"
                f"{libelle_valeur} : %{{z:.1f}} %<br>"
                "Opérations : %{customdata:,.0f}<extra></extra>"
            ),
            xgap=2,
            ygap=2,
        )
    )
    colonnes = [str(c) for c in valeurs.columns]
    # Libellés longs coupés en lignes : ils restent horizontaux, donc lisibles.
    figure.update_xaxes(
        title=textes.libelle_x, side="bottom", tickangle=0, tickvals=colonnes,
        ticktext=["<br>".join(textwrap.wrap(c, LARGEUR_LIBELLE)) for c in colonnes],
    )
    figure.update_yaxes(title=textes.libelle_y, autorange="reversed")
    return appliquer_charte(figure, textes)


def boites_quartiles(
    resume: pd.DataFrame,
    groupe: str,
    textes: TextesFigure,
    horizontal: bool = False,
) -> go.Figure:
    """Boîtes à moustaches à partir de quartiles déjà calculés.

    Boîte = 1er à 3e quartile, trait = médiane, moustaches = 10e et 90e
    centiles. `textes.libelle_x` nomme les groupes, `textes.libelle_y` la valeur.
    """
    if resume.empty:
        return figure_vide(textes.titre)
    groupes = [str(g) for g in resume[groupe]]
    stats = {
        "q1": resume["q1"], "median": resume["mediane"], "q3": resume["q3"],
        "lowerfence": resume["p10"], "upperfence": resume["p90"],
    }
    position = {"y": groupes} if horizontal else {"x": groupes}
    figure = go.Figure(
        go.Box(
            **position, **stats,
            orientation="h" if horizontal else "v",
            marker_color=COULEUR_SERIE,
            fillcolor=COULEUR_SERIE_CLAIRE,
            customdata=resume["operations"],
            hovertemplate=(
                "%{" + ("y" if horizontal else "x") + "}<br>"
                "Opérations : %{customdata:,.0f}<extra></extra>"
            ),
            name="",
        )
    )
    axe_valeur = {"title": textes.libelle_y, "rangemode": "tozero"}
    if horizontal:
        figure.update_xaxes(**axe_valeur)
        figure.update_yaxes(title=textes.libelle_x, autorange="reversed")
    else:
        figure.update_yaxes(**axe_valeur)
        figure.update_xaxes(title=textes.libelle_x)
    figure.update_layout(showlegend=False)
    return appliquer_charte(figure, textes)


def histogramme(
    valeurs: pd.Series,
    textes: TextesFigure,
    bornes: tuple[float, float, float],
) -> go.Figure:
    """Histogramme d'une variable continue ; `bornes` = (début, fin, largeur de classe)."""
    if valeurs.dropna().empty:
        return figure_vide(textes.titre)
    debut, fin, largeur_classe = bornes
    figure = go.Figure(
        go.Histogram(
            x=valeurs,
            xbins={"start": debut, "end": fin, "size": largeur_classe},
            marker={"color": COULEUR_SERIE, "line": {"color": COULEUR_FOND, "width": 1}},
            hovertemplate=(
                f"{textes.libelle_x} : %{{x}}<br>Opérations : %{{y:,.0f}}<extra></extra>"
            ),
        )
    )
    figure.update_xaxes(title=textes.libelle_x, range=[debut, fin])
    figure.update_yaxes(title=textes.libelle_y or "Nombre d'opérations")
    figure.update_layout(bargap=0.02)
    return appliquer_charte(figure, textes)


def courbes(
    donnees: pd.DataFrame,
    colonnes: tuple[str, str, str],
    couleurs: dict[str, str],
    textes: TextesFigure,
    etiquettes_x: dict[int, str] | None = None,
) -> go.Figure:
    """Une courbe par série ; `colonnes` = (abscisse, ordonnée, série)."""
    if donnees.empty:
        return figure_vide(textes.titre)
    x, y, serie = colonnes
    figure = go.Figure()
    for nom, groupe in donnees.groupby(serie, observed=True, sort=False):
        figure.add_trace(
            go.Scatter(
                x=groupe[x], y=groupe[y], name=str(nom), mode="lines+markers",
                line={"color": couleurs.get(str(nom)), "width": 2},
                marker={"size": 5},
                hovertemplate=f"{nom}<br>%{{x}} : %{{y:,.0f}}<extra></extra>",
            )
        )
    if etiquettes_x:
        figure.update_xaxes(tickvals=list(etiquettes_x), ticktext=list(etiquettes_x.values()))
    figure.update_xaxes(title=textes.libelle_x)
    figure.update_yaxes(title=textes.libelle_y, rangemode="tozero")
    return appliquer_charte(figure, textes)


def barres_horizontales(
    donnees: pd.DataFrame,
    colonnes: tuple[str, str],
    textes: TextesFigure,
    format_valeur: str = ".1f",
    couleurs: dict[str, str] | None = None,
    *,
    trier: bool = True,
) -> go.Figure:
    """Barres horizontales ; `colonnes` = (catégorie, valeur).

    Triées par valeur, sauf si `trier=False` (ordre du tableau conservé, de
    haut en bas). La valeur est écrite au bout de chaque barre ;
    `textes.libelle_x` la nomme.
    """
    categorie, valeur = colonnes
    valides = donnees.dropna(subset=[valeur])
    if valides.empty:
        return figure_vide(textes.titre)
    # Plotly trace la première ligne en bas : on inverse l'ordre si non trié.
    valides = valides.sort_values(valeur) if trier else valides.iloc[::-1]
    noms = [str(n) for n in valides[categorie]]
    palette = couleurs or {}
    avec_effectifs = "operations" in valides
    figure = go.Figure(
        go.Bar(
            x=valides[valeur], y=noms, orientation="h",
            marker_color=[palette.get(n, COULEUR_SERIE) for n in noms],
            text=valides[valeur], texttemplate=f"%{{text:{format_valeur}}}",
            textposition="outside", cliponaxis=False,
            customdata=valides.get("operations"),
            hovertemplate=(
                f"%{{y}}<br>{textes.libelle_x} : %{{x:{format_valeur}}}"
                + ("<br>Opérations : %{customdata:,.0f}" if avec_effectifs else "")
                + "<extra></extra>"
            ),
        )
    )
    maximum = float(valides[valeur].max())
    figure.update_xaxes(
        title=textes.libelle_x, range=[0, maximum * MARGE_ETIQUETTES if maximum > 0 else 1]
    )
    figure.update_yaxes(title="")
    figure.update_layout(showlegend=False)
    return appliquer_charte(figure, textes)


def barres_groupees(
    valeurs: pd.DataFrame,
    textes: TextesFigure,
    couleurs: dict[str, str],
) -> go.Figure:
    """Barres côte à côte : une série par ligne de `valeurs`, un groupe par colonne."""
    if valeurs.empty or valeurs.isna().all().all():
        return figure_vide(textes.titre)
    figure = go.Figure()
    for serie, ligne in valeurs.iterrows():
        figure.add_trace(
            go.Bar(
                x=[str(c) for c in valeurs.columns], y=ligne.to_numpy(dtype=float),
                name=str(serie), marker_color=couleurs.get(str(serie)),
                text=ligne.to_numpy(dtype=float), texttemplate="%{text:.1f} %",
                textposition="outside", cliponaxis=False,
                hovertemplate=f"{serie}<br>%{{x}} : %{{y:.1f}} %<extra></extra>",
            )
        )
    maximum = float(valeurs.max().max())
    figure.update_xaxes(title=textes.libelle_x)
    figure.update_yaxes(
        title=textes.libelle_y, range=[0, maximum * MARGE_ETIQUETTES if maximum > 0 else 1]
    )
    figure.update_layout(barmode="group")
    return appliquer_charte(figure, textes)
