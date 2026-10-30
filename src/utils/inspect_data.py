
#fichier inspect_data.py
from pathlib import Path

import pandas as pd

from config import CSV_PATHS

REPORT_PATH = Path("data/inspection_rapport.txt")


def inspect_file(name, path):
    print(f"\n{'=' * 60}")
    print(f"FICHIER : {name}")
    print(f"{'=' * 60}")

    if not path.is_file():
        print(f"Fichier absent : {path}")
        return

    print(f"Taille : {path.stat().st_size / (1024 ** 2):.1f} Mo")

    # Lecture par blocs pour limiter la mémoire utilisée.
    missing_counts = None
    row_count = 0
    first_columns = None
    first_date = None
    last_date = None
    categories = {}

    for chunk in pd.read_csv(
        path,
        chunksize=50_000,
        low_memory=False,
    ):
        row_count += len(chunk)

        if first_columns is None:
            first_columns = list(chunk.columns)
            missing_counts = pd.Series(0, index=chunk.columns, dtype="int64")

        missing_counts += chunk.isna().sum()

        # Dates disponibles dans les fichiers concernés.
        date_column = next(
            (col for col in ("date", "date_heure_reception_alerte")
             if col in chunk.columns),
            None,
        )
        if date_column:
            dates = pd.to_datetime(chunk[date_column], errors="coerce")
            valid_dates = dates.dropna()
            if not valid_dates.empty:
                current_min = valid_dates.min()
                current_max = valid_dates.max()
                first_date = min(first_date, current_min) if first_date is not None else current_min
                last_date = max(last_date, current_max) if last_date is not None else current_max

        for column in ("categorie_flotteur", "evenement"):
            if column in chunk.columns:
                counts = chunk[column].fillna("[MANQUANT]").value_counts()
                if column not in categories:
                    categories[column] = {}
                for value, count in counts.items():
                    categories[column][str(value)] = (
                        categories[column].get(str(value), 0) + int(count)
                    )

    print(f"Nombre de lignes : {row_count:,}".replace(",", " "))
    print(f"Nombre de colonnes : {len(first_columns)}")

    print("\nValeurs manquantes par colonne :")
    missing = missing_counts[missing_counts > 0].sort_values(ascending=False)
    if missing.empty:
        print("Aucune")
    else:
        for column, count in missing.items():
            percentage = count / row_count * 100
            print(f"- {column}: {count:,} ({percentage:.2f} %)".replace(",", " "))

    if first_date is not None:
        print(f"\nPériode des dates : {first_date} à {last_date}")

    for column, values in categories.items():
        print(f"\nValeurs possibles de {column} :")
        for value, count in sorted(values.items()):
            print(f"- {value}: {count:,}".replace(",", " "))


def main():
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    import contextlib
    import io

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        print("RAPPORT D'INSPECTION DES DONNÉES SECMAR")
        print("Inspection en lecture seule : aucun CSV ni SQLite modifié.")

        for name, path in CSV_PATHS.items():
            inspect_file(name, path)

    report = buffer.getvalue()
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(report)
    print(f"\nRapport enregistré dans : {REPORT_PATH}")


if __name__ == "__main__":
    main()
