"""Messages « à retenir » affichés en haut de chaque onglet.

Les messages sont recalculés à chaque changement de filtre : ils décrivent la
sélection en cours. Ils décrivent des opérations déclenchées, pas un risque
mesuré : leur formulation reste prudente (« on observe »).
"""

from collections.abc import Callable
from dataclasses import dataclass

import pandas as pd

from config import CLASSES_MER, CLASSES_VENT, GRAVITES, NOMS_MOIS_LONGS

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


def messages_conditions(donnees: pd.DataFrame) -> list[Message]:
    """Messages de l'onglet « Conditions » : mer forte, vent fort, données notées."""
    messages: list[Message] = []
    calme, tres_forte = next(iter(CLASSES_MER)), list(CLASSES_MER)[-1]
    mer_calme = donnees[donnees["classe_mer"] == calme]
    mer_forte = donnees[donnees["classe_mer"] == tres_forte]
    if min(len(mer_calme), len(mer_forte)) >= EFFECTIF_MINIMAL_MESSAGE:
        taux_forte = taux_pour_mille(victimes_graves(mer_forte))
        taux_calme = taux_pour_mille(victimes_graves(mer_calme))
        if 0 < taux_calme < taux_forte:
            messages.append(
                Message(
                    f"Mer très forte : mortalité × {formater(taux_forte / taux_calme, 1)}",
                    f"Par mer très forte, {formater(taux_forte)} opérations sur 1 000 comptent "
                    f"un décès ou un disparu, contre {formater(taux_calme)} par mer calme.",
                    "grave",
                )
            )
    faible, forts = next(iter(CLASSES_VENT)), list(CLASSES_VENT)[2:]
    vent_faible = donnees[donnees["classe_vent"] == faible]
    vent_fort = donnees[donnees["classe_vent"].isin(forts)]
    if donnees["famille"].nunique() > 1 and min(len(vent_faible), len(vent_fort)) >= (
        EFFECTIF_MINIMAL_MESSAGE
    ):
        part_fort = part_en_pourcent(vent_fort["famille"].eq("Accident de navire"))
        part_faible = part_en_pourcent(vent_faible["famille"].eq("Accident de navire"))
        if part_fort > part_faible:
            messages.append(
                Message(
                    "Vent fort : plus d'accidents de navire",
                    f"Par vent de force 6 et plus, les accidents de navire représentent "
                    f"{formater(part_fort)} % des opérations, contre {formater(part_faible)} % "
                    "par vent faible.",
                    "alerte",
                )
            )
    if len(donnees) >= EFFECTIF_MINIMAL_MESSAGE:
        renseigne = part_en_pourcent(donnees["classe_vent"].notna())
        messages.append(
            Message(
                "Des conditions pas toujours notées",
                f"La force du vent est renseignée pour {formater(renseigne)} % des opérations "
                "sélectionnées : les graphiques portent sur celles-ci.",
            )
        )
    return messages


def _taux_par_famille(donnees: pd.DataFrame, colonnes: list[str], pour: int) -> pd.Series:
    """Somme des colonnes rapportée à `pour` opérations, par famille assez représentée."""
    groupes = donnees.assign(_total=donnees[colonnes].sum(axis=1)).groupby(
        "famille", observed=True
    )["_total"]
    taux = groupes.mean() * pour
    return taux[groupes.size() >= EFFECTIF_MINIMAL_MESSAGE].sort_values(ascending=False)


def messages_consequences(donnees: pd.DataFrame) -> list[Message]:
    """Messages de l'onglet « Conséquences » : mortalité, blessés, part avec victimes."""
    if len(donnees) < EFFECTIF_MINIMAL_MESSAGE:
        return []
    messages: list[Message] = []
    deces = _taux_par_famille(donnees, ["personnes_decedees", "personnes_disparues"], 1000)
    if len(deces) >= 2:
        messages.append(
            Message(
                f"{deces.index[0]} : la famille la plus meurtrière",
                f"{formater(deces.iloc[0])} décès ou disparus pour 1 000 opérations, "
                f"contre {formater(deces.iloc[1])} pour « {deces.index[1]} », la suivante.",
                "grave",
            )
        )
    blesses = _taux_par_famille(donnees, ["personnes_blessees"], 100)
    if len(blesses) >= 1:
        messages.append(
            Message(
                f"{blesses.index[0]} : le plus de blessés",
                f"{formater(blesses.iloc[0])} personnes blessées pour 100 opérations.",
                "alerte",
            )
        )
    avec_victimes = part_en_pourcent(donnees["gravite"].ne(GRAVITES[0]))
    messages.append(
        Message(
            "Une minorité d'opérations avec victimes",
            f"{formater(avec_victimes, 1)} % des opérations sélectionnées ont fait au moins "
            "un blessé, un décès ou un disparu.",
        )
    )
    return messages
