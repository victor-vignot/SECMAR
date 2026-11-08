"""Inspection en lecture seule des CSV SECMAR.

Produit `data/inspection_rapport.txt` : taille, nombre de lignes, valeurs
manquantes, période couverte et modalités des principales colonnes.
Lancement : `uv run python -m src.utils.inspect_data`
"""

import contextlib
import io
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from config import CSV_PATHS, DATA_DIR

REPORT_PATH = DATA_DIR / "inspection_rapport.txt"
COLONNES_DATE = ("date", "date_heure_reception_alerte")
COLONNES_MODALITES = ("categorie_flotteur", "evenement")


@dataclass
class Inspection:
    """Statistiques cumulées bloc par bloc sur un fichier CSV."""

    lignes: int = 0
    colonnes: list[str] = field(default_factory=list)
    manquants: pd.Series | None = None
    premiere_date: pd.Timestamp | None = None
    derniere_date: pd.Timestamp | None = None
    modalites: dict[str, dict[str, int]] = field(default_factory=dict)


def _mettre_a_jour_dates(inspection: Inspection, bloc: pd.DataFrame) -> None:
    """Met à jour la période couverte avec les dates d'un bloc."""
    colonne = next((c for c in COLONNES_DATE if c in bloc.columns), None)
    if colonne is None:
        return
    dates = pd.to_datetime(bloc[colonne], errors="coerce").dropna()
    if dates.empty:
        return
    debut, fin = dates.min(), dates.max()
    inspection.premiere_date = min(filter(None, [inspection.premiere_date, debut]))
    inspection.derniere_date = max(filter(None, [inspection.derniere_date, fin]))


def _mettre_a_jour_modalites(inspection: Inspection, bloc: pd.DataFrame) -> None:
    """Additionne les effectifs des modalités des colonnes suivies."""
    for colonne in COLONNES_MODALITES:
        if colonne not in bloc.columns:
            continue
        compteur = inspection.modalites.setdefault(colonne, {})
        for valeur, nombre in bloc[colonne].fillna("[MANQUANT]").value_counts().items():
            compteur[str(valeur)] = compteur.get(str(valeur), 0) + int(nombre)


def inspecter(path: Path) -> Inspection:
    """Parcourt un CSV par blocs de 50 000 lignes pour limiter la mémoire."""
    inspection = Inspection()
    for bloc in pd.read_csv(path, chunksize=50_000, low_memory=False):
        inspection.lignes += len(bloc)
        if inspection.manquants is None:
            inspection.colonnes = list(bloc.columns)
            inspection.manquants = pd.Series(0, index=bloc.columns, dtype="int64")
        inspection.manquants += bloc.isna().sum()
        _mettre_a_jour_dates(inspection, bloc)
        _mettre_a_jour_modalites(inspection, bloc)
    return inspection


def afficher(inspection: Inspection) -> None:
    """Affiche le résultat d'une inspection."""
    print(f"Nombre de lignes : {inspection.lignes:,}".replace(",", " "))
    print(f"Nombre de colonnes : {len(inspection.colonnes)}")
    print("\nValeurs manquantes par colonne :")
    manquants = inspection.manquants if inspection.manquants is not None else pd.Series()
    manquants = manquants[manquants > 0].sort_values(ascending=False)
    if manquants.empty:
        print("Aucune")
    for colonne, nombre in manquants.items():
        pourcentage = nombre / inspection.lignes * 100
        print(f"- {colonne}: {nombre:,} ({pourcentage:.2f} %)".replace(",", " "))
    if inspection.premiere_date is not None:
        print(f"\nPériode des dates : {inspection.premiere_date} à {inspection.derniere_date}")
    for colonne, valeurs in inspection.modalites.items():
        print(f"\nValeurs possibles de {colonne} :")
        for valeur, nombre in sorted(valeurs.items()):
            print(f"- {valeur}: {nombre:,}".replace(",", " "))


def inspect_file(name: str, path: Path) -> None:
    """Inspecte un fichier et affiche son rapport."""
    print(f"\n{'=' * 60}\nFICHIER : {name}\n{'=' * 60}")
    if not path.is_file():
        print(f"Fichier absent : {path}")
        return
    print(f"Taille : {path.stat().st_size / (1024 ** 2):.1f} Mo")
    afficher(inspecter(path))


def main() -> None:
    """Inspecte tous les CSV et enregistre le rapport texte."""
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    tampon = io.StringIO()
    with contextlib.redirect_stdout(tampon):
        print("RAPPORT D'INSPECTION DES DONNÉES SECMAR")
        print("Inspection en lecture seule : aucun CSV ni SQLite modifié.")
        for name, path in CSV_PATHS.items():
            inspect_file(name, path)
    rapport = tampon.getvalue()
    REPORT_PATH.write_text(rapport, encoding="utf-8")
    print(rapport)
    print(f"\nRapport enregistré dans : {REPORT_PATH}")


if __name__ == "__main__":
    main()
