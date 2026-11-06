"""Messages « à retenir » affichés en haut de chaque onglet.

Les messages sont recalculés à chaque changement de filtre : ils décrivent la
sélection en cours. Ils décrivent des opérations déclenchées, pas un risque
mesuré : leur formulation reste prudente (« on observe »).
"""

from collections.abc import Callable
from dataclasses import dataclass

import pandas as pd

from config import NOMS_MOIS_LONGS

# Tons possibles : information, point de vigilance, conséquence grave.
TONS_MESSAGES = ("info", "alerte", "grave")

# En dessous de cet effectif, un message ne serait pas fiable : il n'est pas affiché.
EFFECTIF_MINIMAL_MESSAGE = 100


@dataclass(frozen=True)
class Message:
    """Un message court : un titre et une phrase chiffrée."""

    titre: str
    texte: str
    ton: str = "info"

    def __post_init__(self) -> None:
        if self.ton not in TONS_MESSAGES:
            raise ValueError(f"Ton inconnu : {self.ton!r}")


FonctionMessages = Callable[[pd.DataFrame], list[Message]]


def formater(valeur: float, decimales: int = 0) -> str:
    """Nombre au format français : espace pour les milliers, virgule décimale."""
    texte = f"{valeur:,.{decimales}f}"
    return texte.replace(",", " ").replace(".", ",")


def taux_pour_mille(masque: pd.Series) -> float:
    """Nombre d'opérations vérifiant la condition, pour 1 000 opérations."""
    return float(masque.mean() * 1000) if len(masque) else 0.0


def part_en_pourcent(masque: pd.Series) -> float:
    """Part des opérations vérifiant la condition, en %."""
    return float(masque.mean() * 100) if len(masque) else 0.0


def victimes_graves(donnees: pd.DataFrame) -> pd.Series:
    """Vrai pour les opérations ayant fait au moins un décès ou un disparu."""
    return (donnees["personnes_decedees"] + donnees["personnes_disparues"]).gt(0)


def messages_quand(donnees: pd.DataFrame) -> list[Message]:
    """Messages de l'onglet « Quand ? » : mois de pointe, été, saisonnalité."""
    if len(donnees) < EFFECTIF_MINIMAL_MESSAGE:
        return []
    par_mois = donnees["mois"].value_counts()
    mois_pic = int(par_mois.idxmax())
    part_pic = par_mois.max() / len(donnees) * 100
    messages = [
        Message(
            f"{NOMS_MOIS_LONGS[mois_pic].capitalize()}, le mois le plus chargé",
            f"{formater(part_pic)} % des opérations de la sélection ont lieu en "
            f"{NOMS_MOIS_LONGS[mois_pic]}, contre 8 % si elles étaient réparties "
            "également sur l'année.",
            "alerte",
        ),
        Message(
            "L'été concentre l'activité",
            f"{formater(part_en_pourcent(donnees['saison'].eq('Été')))} % des opérations "
            "ont lieu en été (juin à août), contre "
            f"{formater(part_en_pourcent(donnees['saison'].eq('Hiver')))} % en hiver.",
        ),
    ]
    saisonniere = _famille_la_plus_saisonniere(donnees)
    if saisonniere is not None:
        famille, rapport, pic, creux = saisonniere
        messages.append(
            Message(
                f"{famille} : l'activité la plus saisonnière",
                f"{formater(rapport, 1)} fois plus d'opérations en {NOMS_MOIS_LONGS[pic]} "
                f"qu'en {NOMS_MOIS_LONGS[creux]}.",
            )
        )
    return messages


def _famille_la_plus_saisonniere(
    donnees: pd.DataFrame,
) -> tuple[str, float, int, int] | None:
    """Famille dont l'écart entre mois de pointe et mois creux est le plus fort.

    Seules les familles assez représentées et présentes les 12 mois comptent.
    """
    comptes = donnees.groupby(["famille", "mois"], observed=True).size().unstack(fill_value=0)
    comptes = comptes[(comptes.sum(axis=1) >= EFFECTIF_MINIMAL_MESSAGE) & (comptes.min(axis=1) > 0)]
    if comptes.empty or comptes.shape[1] < 12:
        return None
    rapports = comptes.max(axis=1) / comptes.min(axis=1)
    famille = rapports.idxmax()
    ligne = comptes.loc[famille]
    return str(famille), float(rapports.max()), int(ligne.idxmax()), int(ligne.idxmin())
