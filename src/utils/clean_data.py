
#fichier clean_data.py
import sqlite3

import pandas as pd

from config import CSV_PATHS, DB_PATH, DATA_DIR


def main():
    """Importe les CSV SECMAR dans SQLite sans nettoyage."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    missing_files = [
        path for path in CSV_PATHS.values()
        if not path.is_file()
    ]

    if missing_files:
        missing = "\n".join(str(path) for path in missing_files)
        raise FileNotFoundError(
            f"Fichiers CSV manquants dans data/raw/ :\n{missing}"
        )

    with sqlite3.connect(DB_PATH) as connection:
        for name, csv_path in CSV_PATHS.items():
            table_name = f"raw_{name}"

            print(f"Import de {csv_path.name} vers {table_name}...")

            chunks = pd.read_csv(
                csv_path,
                chunksize=50_000,
                low_memory=False,
            )

            first_chunk = True

            for chunk in chunks:
                chunk.to_sql(
                    table_name,
                    connection,
                    if_exists="replace" if first_chunk else "append",
                    index=False,
                )
                first_chunk = False

            print(f"Table {table_name} importée.")

    print(f"Import terminé. Base créée : {DB_PATH}")


if __name__ == "__main__":
    main()
