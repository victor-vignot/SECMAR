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
