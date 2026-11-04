"""Regroupement harmonisé des événements SECMAR en familles stables.

La colonne `categorie_evenement` change de nomenclature lors du passage du
système SECMARweb au système SEAMIS (2019-2021) : les fausses alertes et les
avaries y disparaissent presque. Le détail `evenement` est, lui, stable. On
regroupe donc les 68 valeurs de `evenement` en familles comparables dans le
temps.
"""

FAMILLE_INCONNUE = "Non renseigné"

# Chaque famille liste les valeurs exactes de la colonne `evenement`.
FAMILLES_EVENEMENTS: dict[str, tuple[str, ...]] = {
    "Avarie ou panne": (
        "Avarie du système de propulsion",
        "Avarie électrique",
        "Avarie de l'appareil à gouverner",
        "Avarie des systèmes de communication",
        "Avarie de gréement",
        "Démâtage",
        "Panne de carburant",
        "Immobilisé dans engins / hélice engagée",
        "Encalminage",
        "Absence d'un moyen de communication",
        "Mouillage immobilisé",
    ),
    "Accident de navire": (
        "Abordage",
        "Collision",
        "Heurt",
        "Échouement",
        "Talonnage",
        "Chavirement",
        "Naufrage",
        "Voie d'eau",
        "Incendie",
        "Explosion",
        "Perte de stabilité / Ripage de cargaison",
        "Désarrimage cargaison",
        "Perte de pontée",
        "Rupture de mouillage",
        "Accident en mer",
    ),
    "Difficulté de navigation": (
        "Difficulté de manoeuvre",
        "Sans avarie en dérive",
        "Sans avarie inexpérience",
        "Inexpérience",
        "Incertitude sur la position",
        "Isolement par la marée / Envasé",
    ),
    "Personne à la mer ou disparue": (
        "Homme à la mer",
        "Disparu en mer",
        "Chute falaise / Emporté par une lame",
        "Découverte de corps",
        "Suicide",
    ),
    "Baignade et loisirs": (
        "Baignade",
        "Plongée avec bouteille",
        "Plongée en apnée",
        "Chasse sous-marine",
        "Ski nautique",
        "Loisir nautique",
    ),
    "Médical": (
        "Blessé EvaMed",
        "Blessé EvaSan",
        "Blessé avec déroutement",
        "Blessé avec soin sans déroutement",
        "Blessé projection d'une équipe médicale",
        "Malade EvaMed",
        "Malade EvaSan",
        "Malade avec déroutement",
        "Malade avec soin sans déroutement",
        "Malade projection d'une équipe médicale",
        "Problème médical",
        "Accident corporel",
        "Transport sanitaire île-continent",
    ),
    "Fausse alerte ou situation indéterminée": (
        "Toutes fausses alertes",
        "Incertitude",
        "Situation indéterminée",
    ),
    "Sûreté et migrations": (
        "Immigration clandestine",
        "Acte de piraterie / terrorisme",
        "Trouble à l'ordre public",
        "Découverte d'explosif",
        "Explosif dans engin",
        "Engin dangereux à bord",
    ),
    "Autre": (
        "Autre événement",
        "Autre accident",
        "Accident aéronautique",
    ),
}

# Événements correspondant à une évacuation sanitaire ou médicale.
# Ils n'existent que dans le système SECMARweb (jusqu'en 2020 environ).
EVENEMENTS_EVACUATION = (
    "Blessé EvaMed",
    "Blessé EvaSan",
    "Malade EvaMed",
    "Malade EvaSan",
)

# Ordre d'affichage des familles dans les graphiques et le filtre.
ORDRE_FAMILLES: list[str] = [*FAMILLES_EVENEMENTS, FAMILLE_INCONNUE]


def construire_correspondance() -> dict[str, str]:
    """Retourne le dictionnaire `evenement -> famille`.

    Lève une erreur si un même événement est rangé dans deux familles, ce qui
    rendrait le regroupement ambigu.
    """
    correspondance: dict[str, str] = {}
    for famille, evenements in FAMILLES_EVENEMENTS.items():
        for evenement in evenements:
            if evenement in correspondance:
                raise ValueError(
                    f"Événement classé deux fois : {evenement!r}"
                )
            correspondance[evenement] = famille
    return correspondance


CORRESPONDANCE_FAMILLES = construire_correspondance()


def famille_de(evenement: str | None) -> str:
    """Retourne la famille d'un événement, ou « Non renseigné »."""
    if evenement is None:
        return FAMILLE_INCONNUE
    return CORRESPONDANCE_FAMILLES.get(evenement, FAMILLE_INCONNUE)
