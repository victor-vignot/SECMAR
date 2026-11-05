"""Données de test partagées : un petit échantillon fictif au format `cleaned`."""

import numpy as np
import pandas as pd
import pytest

from config import CLASSES_MER, CLASSES_VENT, GRAVITES, SAISONS
from src.utils.familles import EVENEMENTS_EVACUATION, FAMILLES_EVENEMENTS
from src.utils.queries import typer_categories


@pytest.fixture(name="echantillon")
def fixture_echantillon() -> pd.DataFrame:
    """2 000 opérations fictives reproductibles, mêmes colonnes que le dashboard."""
    generateur = np.random.default_rng(42)
    taille = 2_000

    def tirer(valeurs: list[str]) -> np.ndarray:
        return generateur.choice(valeurs, size=taille)

    mois = generateur.integers(1, 13, size=taille)
    correspondance_saisons = {m: s for s, ms in SAISONS.items() for m in ms}
    donnees = pd.DataFrame({
        "operation_id": np.arange(taille),
        "annee": generateur.integers(2005, 2026, size=taille),
        "mois": mois,
        "saison": [correspondance_saisons[m] for m in mois],
        "cross": tirer(["Étel", "La Garde", "Corsen", "Gris-Nez"]),
        "departement": tirer(["Var", "Finistère", "Morbihan", "Manche"]),
        "est_metropolitain": 1,
        "zone": tirer(["Atlantique", "Méditerranée", "Manche - mer du Nord"]),
        "famille": tirer(list(FAMILLES_EVENEMENTS)),
        # Quelques évacuations sanitaires parmi des baignades.
        "evenement": tirer(["Baignade"] * 9 + list(EVENEMENTS_EVACUATION)),
        "est_evacuation": generateur.integers(0, 2, size=taille),
        "latitude": generateur.uniform(42, 51, size=taille),
        "longitude": generateur.uniform(-5, 8, size=taille),
        "vent_force": generateur.integers(0, 10, size=taille),
        "mer_force": generateur.integers(0, 7, size=taille),
        "classe_vent": tirer(list(CLASSES_VENT)),
        "classe_mer": tirer(list(CLASSES_MER)),
        "duree_heures": generateur.exponential(3, size=taille),
        "distance_cote_mn": generateur.exponential(5, size=taille),
        "personnes_impliquees": generateur.integers(0, 6, size=taille),
        "personnes_impliquees_sans_clandestins": generateur.integers(0, 6, size=taille),
        "personnes_blessees": generateur.integers(0, 2, size=taille),
        "personnes_decedees": generateur.binomial(1, 0.02, size=taille),
        "personnes_disparues": generateur.binomial(1, 0.01, size=taille),
        "personnes_secourues": generateur.integers(0, 4, size=taille),
        "gravite": tirer(GRAVITES),
    })
    return typer_categories(donnees)
