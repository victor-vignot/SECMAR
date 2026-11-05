"""Agrégations statistiques réutilisées par tous les graphiques.

Les graphiques ne calculent rien eux-mêmes : ils reçoivent les tableaux
produits ici. Une même fonction sert ainsi à plusieurs axes d'analyse.
"""

from dataclasses import dataclass

import pandas as pd

from config import EFFECTIF_MINIMAL


@dataclass(frozen=True)
class TableauCroise:
    """Résultat d'un croisement : pourcentages et effectifs par groupe."""

    pourcentages: pd.DataFrame  # lignes = catégories, colonnes = groupes
    effectifs: pd.DataFrame  # nombre d'opérations par case
    totaux: pd.Series  # nombre d'opérations par groupe


def profil_croise(
    donnees: pd.DataFrame,
    groupe: str,
    categorie: str,
    effectif_min: int = EFFECTIF_MINIMAL,
) -> TableauCroise:
    """Répartition (en %) des catégories à l'intérieur de chaque groupe.

    Chaque colonne (groupe) somme à 100 %. Les groupes de moins de
    `effectif_min` opérations sont masqués (pourcentages peu fiables).
    Les lignes sans groupe ou sans catégorie sont ignorées.
    """
    valides = donnees.dropna(subset=[groupe, categorie])
    effectifs = (
        valides.groupby([categorie, groupe], observed=False)
        .size()
        .unstack(groupe, fill_value=0)
    )
    totaux = effectifs.sum(axis=0)
    pourcentages = effectifs.div(totaux.where(totaux > 0), axis=1) * 100
    pourcentages = pourcentages.loc[:, totaux >= effectif_min]
    return TableauCroise(pourcentages, effectifs[pourcentages.columns], totaux)


def taux_par_cases(
    donnees: pd.DataFrame,
    ligne: str,
    colonne: str,
    condition: pd.Series,
    effectif_min: int = EFFECTIF_MINIMAL,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Part (en %) des opérations vérifiant `condition`, par case ligne × colonne.

    Retourne (taux, effectifs) ; les cases sous `effectif_min` sont masquées.
    """
    valides = donnees.dropna(subset=[ligne, colonne]).assign(
        _condition=condition.astype(float)
    )
    groupes = valides.groupby([ligne, colonne], observed=False)["_condition"]
    effectifs = groupes.size().unstack(colonne, fill_value=0)
    taux = (groupes.mean() * 100).unstack(colonne)
    return taux.where(effectifs >= effectif_min), effectifs


def indicateurs_par_groupe(
    donnees: pd.DataFrame,
    groupe: str,
    colonnes: list[str],
    pour: int = 1,
) -> pd.DataFrame:
    """Total et moyenne (pour `pour` opérations) de chaque colonne, par groupe."""
    agregats = donnees.groupby(groupe, observed=True).agg(
        operations=(colonnes[0], "size"),
        **{f"total_{c}": (c, "sum") for c in colonnes},
        **{f"moyenne_{c}": (c, "mean") for c in colonnes},
    )
    for colonne in colonnes:
        agregats[f"taux_{colonne}"] = agregats[f"moyenne_{colonne}"] * pour
    return agregats.reset_index()


def quartiles_par_groupe(
    donnees: pd.DataFrame,
    groupe: str,
    valeur: str,
    effectif_min: int = EFFECTIF_MINIMAL,
) -> pd.DataFrame:
    """Statistiques de boîte à moustaches calculées à l'avance.

    Moustaches = 10e et 90e centiles : calculer les quartiles ici évite
    d'envoyer des centaines de milliers de points au navigateur.
    """
    valides = donnees.dropna(subset=[groupe, valeur])
    groupes = valides.groupby(groupe, observed=True)[valeur]
    resume = pd.DataFrame({
        "operations": groupes.size(),
        "p10": groupes.quantile(0.10),
        "q1": groupes.quantile(0.25),
        "mediane": groupes.median(),
        "q3": groupes.quantile(0.75),
        "p90": groupes.quantile(0.90),
    })
    return resume[resume["operations"] >= effectif_min].reset_index()


def comptage_par(donnees: pd.DataFrame, colonnes: list[str]) -> pd.DataFrame:
    """Nombre d'opérations pour chaque combinaison des colonnes données."""
    return (
        donnees.dropna(subset=colonnes)
        .groupby(colonnes, observed=True)
        .size()
        .reset_index(name="operations")
    )


def principales_modalites(donnees: pd.DataFrame, colonne: str, nombre: int) -> list[str]:
    """Les `nombre` valeurs les plus fréquentes d'une colonne."""
    return donnees[colonne].value_counts().head(nombre).index.tolist()
