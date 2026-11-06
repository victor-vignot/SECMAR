"""Messages « à retenir » affichés en haut de chaque onglet.

Les messages sont recalculés à chaque changement de filtre : ils décrivent la
sélection en cours. Ils décrivent des opérations déclenchées, pas un risque
mesuré : leur formulation reste prudente (« on observe »).
"""

from collections.abc import Callable
from dataclasses import dataclass

import pandas as pd

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
