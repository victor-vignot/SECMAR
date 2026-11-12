"""Messages « à retenir » affichés en haut de chaque onglet.

Les messages sont recalculés à chaque changement de filtre : ils décrivent la
sélection en cours. Ils décrivent des opérations déclenchées, pas un risque
mesuré : leur formulation reste prudente (« on observe »).
"""

from collections.abc import Callable
from dataclasses import dataclass

import pandas as pd

from config import (
    CLASSES_MER,
    CLASSES_VENT,
    GRAVITES,
    NOMS_MOIS_LONGS,
    RUPTURES_SAISIE,
    ZONE_INCONNUE,
)
from src.utils.aggregations import CLASSES_DISTANCE, classer_distance

# Tons possibles : information, point de vigilance, conséquence grave.
TONS_MESSAGES = ("info", "alerte", "grave")

# En dessous de cet effectif, un message ne serait pas fiable : il n'est pas affiché.
EFFECTIF_MINIMAL_MESSAGE = 100
FAMILLE_MEDICALE = "Médical"
# Événement le plus fréquent parmi les urgences médicales par mer très forte.
TRANSPORT_ILES = "Transport sanitaire île-continent"


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
    """Messages de l'onglet « Conditions » : mortalité, accidents, urgences médicales."""
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
    medical = message_medical_mer(mer_calme, mer_forte)
    if medical is not None:
        messages.append(medical)
    return messages


def message_medical_mer(mer_calme: pd.DataFrame, mer_forte: pd.DataFrame) -> Message | None:
    """Part des opérations médicales par mer très forte, comparée à la mer calme."""
    if min(len(mer_calme), len(mer_forte)) < EFFECTIF_MINIMAL_MESSAGE:
        return None
    part_forte = part_en_pourcent(mer_forte["famille"].eq(FAMILLE_MEDICALE))
    part_calme = part_en_pourcent(mer_calme["famille"].eq(FAMILLE_MEDICALE))
    if not 0 < part_calme < part_forte:
        return None
    medicales = mer_forte[mer_forte["famille"] == FAMILLE_MEDICALE]
    texte = (
        f"Par mer très forte, {formater(part_forte)} % des opérations sont médicales, "
        f"contre {formater(part_calme)} % par mer calme."
    )
    if len(medicales) >= EFFECTIF_MINIMAL_MESSAGE:
        iles = part_en_pourcent(medicales["evenement"].eq(TRANSPORT_ILES))
        texte += (
            f" {formater(iles)} % de ces urgences sont des transports sanitaires entre "
            "une île et le continent."
        )
    return Message(
        f"Mer forte : part médicale × {formater(part_forte / part_calme, 1)}", texte, "alerte"
    )


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


def messages_duree(donnees: pd.DataFrame) -> list[Message]:
    """Messages de l'onglet « Durée et distance »."""
    messages: list[Message] = []
    calme, tres_forte = next(iter(CLASSES_MER)), list(CLASSES_MER)[-1]
    durees_calme = donnees.loc[donnees["classe_mer"] == calme, "duree_heures"].dropna()
    durees_forte = donnees.loc[donnees["classe_mer"] == tres_forte, "duree_heures"].dropna()
    if min(len(durees_calme), len(durees_forte)) >= EFFECTIF_MINIMAL_MESSAGE:
        longue_forte, longue_calme = durees_forte.quantile(0.9), durees_calme.quantile(0.9)
        if longue_forte > longue_calme:
            messages.append(
                Message(
                    "Mer très forte : des opérations plus longues",
                    f"Par mer très forte, une opération sur dix dure plus de "
                    f"{formater(longue_forte)} h, contre {formater(longue_calme)} h par mer calme.",
                    "alerte",
                )
            )
    distances = donnees["distance_cote_mn"].dropna()
    if len(distances) >= EFFECTIF_MINIMAL_MESSAGE:
        messages.append(
            Message(
                "Un secours de proximité",
                f"En métropole, {formater(part_en_pourcent(distances.le(1)))} % des opérations "
                "ont lieu à moins d'un mille nautique (1,85 km) de la côte.",
            )
        )
        classe_la_plus_grave = _classe_distance_la_plus_grave(donnees)
        if classe_la_plus_grave is not None:
            classe, taux = classe_la_plus_grave
            messages.append(
                Message(
                    f"Mortalité la plus forte : {classe.lower()}",
                    f"{formater(taux)} décès ou disparus pour 1 000 opérations dans cette "
                    "classe de distance, la plus élevée de la sélection (hors opérations "
                    "lointaines).",
                    "grave",
                )
            )
    return messages


def _classe_distance_la_plus_grave(donnees: pd.DataFrame) -> tuple[str, float] | None:
    """Classe de distance où le nombre de décès et disparus par opération est le plus fort."""
    metropole = donnees.dropna(subset=["distance_cote_mn"])
    victimes = metropole["personnes_decedees"] + metropole["personnes_disparues"]
    groupes = victimes.groupby(classer_distance(metropole["distance_cote_mn"]), observed=True)
    taux = (groupes.mean() * 1000)[groupes.size() >= EFFECTIF_MINIMAL_MESSAGE]
    # Les opérations lointaines (relais d'alertes à l'étranger) ne disent rien des
    # risques près de nos côtes : elles ne participent pas à la comparaison.
    taux = taux.drop(CLASSES_DISTANCE[-1], errors="ignore")
    if taux.empty:
        return None
    return str(taux.idxmax()), float(taux.max())


# Un CROSS doit coordonner au moins ce nombre d'opérations pour qu'on décrive son profil.
EFFECTIF_MINIMAL_TERRITOIRE = 300

# Familles trop générales pour caractériser un territoire.
FAMILLES_PEU_PARLANTES = ("Autre", "Non renseigné")


def messages_ou(donnees: pd.DataFrame) -> list[Message]:
    """Messages de l'onglet « Où ? » : CROSS le plus actif, profil distinctif, façade."""
    if len(donnees) < EFFECTIF_MINIMAL_MESSAGE or donnees["cross"].nunique() < 2:
        return []
    par_cross = donnees["cross"].value_counts()
    messages = [
        Message(
            f"{par_cross.index[0]}, le CROSS le plus sollicité",
            f"Il coordonne {formater(par_cross.iloc[0] / len(donnees) * 100)} % des "
            "opérations de la sélection.",
        )
    ]
    distinctif = _profil_distinctif(donnees)
    if distinctif is not None:
        cross, famille, part_locale, part_moyenne = distinctif
        messages.append(
            Message(
                f"{cross} : un profil à part",
                f"« {famille} » y représente {formater(part_locale)} % des opérations, "
                f"contre {formater(part_moyenne)} % sur l'ensemble de la sélection.",
                "alerte",
            )
        )
    zones = donnees[donnees["zone"] != ZONE_INCONNUE]
    taux = victimes_graves(zones).groupby(zones["zone"]).mean() * 1000
    taux = taux[zones["zone"].value_counts().reindex(taux.index) >= EFFECTIF_MINIMAL_MESSAGE]
    if len(taux) >= 2:
        messages.append(
            Message(
                f"{taux.idxmax()} : la zone la plus grave",
                f"{formater(taux.max())} opérations sur 1 000 y comptent un décès ou un "
                f"disparu, contre {formater(taux.min())} pour {taux.idxmin()}.",
                "grave",
            )
        )
    return messages


def _profil_distinctif(donnees: pd.DataFrame) -> tuple[str, str, float, float] | None:
    """Couple (CROSS, famille) le plus sur-représenté par rapport à la moyenne."""
    parts_moyennes = donnees["famille"].value_counts(normalize=True) * 100
    actifs = donnees["cross"].value_counts()
    actifs = actifs[actifs >= EFFECTIF_MINIMAL_TERRITOIRE].index
    parts = (
        donnees[donnees["cross"].isin(actifs)]
        .groupby("cross")["famille"]
        .value_counts(normalize=True)
        .mul(100)
        .rename("part")
        .reset_index()
    )
    parts = parts[~parts["famille"].isin(FAMILLES_PEU_PARLANTES) & parts["part"].ge(5)]
    if parts.empty:
        return None
    parts["rapport"] = parts["part"] / parts["famille"].map(parts_moyennes).astype(float)
    meilleur = parts.loc[parts["rapport"].idxmax()]
    famille = str(meilleur["famille"])
    return str(meilleur["cross"]), famille, float(meilleur["part"]), float(parts_moyennes[famille])


def _message_ruptures(premiere: int, derniere: int) -> Message | None:
    """Avertissement si la période choisie traverse un changement de saisie."""
    traversees = [
        rupture for rupture in RUPTURES_SAISIE if premiere < rupture[0] and derniere > rupture[1]
    ]
    if not traversees:
        return None
    periodes = " et ".join(f"{debut}-{fin}" for debut, fin, _ in traversees)
    explications = " ; ".join(explication for _, _, explication in traversees)
    return Message(
        f"Prudence sur {periodes}",
        f"La façon d'enregistrer les opérations a changé ({explications}) : "
        "une partie des variations vient de la saisie, pas du terrain.",
        "alerte",
    )


def messages_evolution(donnees: pd.DataFrame) -> list[Message]:
    """Messages de l'onglet « Évolution » : tendance, année record, prudence."""
    annees = sorted(int(annee) for annee in donnees["annee"].dropna().unique())
    if len(annees) < 2 or len(donnees) < EFFECTIF_MINIMAL_MESSAGE:
        return []
    par_annee = donnees["annee"].value_counts()
    premiere, derniere = annees[0], annees[-1]
    debut, fin = int(par_annee[premiere]), int(par_annee[derniere])
    sens = "hausse" if fin > debut else "baisse"
    record = int(par_annee.idxmax())
    messages = [
        Message(
            f"Activité en {sens} de {premiere} à {derniere}",
            f"{formater(debut)} opérations en {premiere}, {formater(fin)} en {derniere}, "
            f"soit {formater(fin / debut, 1)} fois le niveau de départ.",
            "alerte" if sens == "hausse" else "info",
        ),
        Message(
            f"{record} : l'année record",
            f"{formater(par_annee.max())} opérations, le plus haut niveau de la sélection.",
        ),
    ]
    prudence = _message_ruptures(premiere, derniere)
    if prudence is not None:
        messages.append(prudence)
    return messages
