"""Accès à la base SQLite et gestion de son archive compressée."""

import lzma
import shutil
import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager
from pathlib import Path

from config import DB_ARCHIVE_PATH, DB_PATH, TABLE_CLEANED, TABLE_RAW

# Seules ces tables sont placées dans l'archive versionnée.
TABLES_ARCHIVEES = (TABLE_RAW, TABLE_CLEANED)


@contextmanager
def ouvrir_connexion(
    chemin_base: Path = DB_PATH,
) -> Iterator[sqlite3.Connection]:
    """Ouvre une connexion en lecture seule et la ferme à coup sûr.

    `with sqlite3.connect(...)` valide la transaction mais ne ferme pas la
    connexion : on utilise `closing` pour éviter les `ResourceWarning`.
    """
    uri = f"file:{chemin_base.as_posix()}?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as connexion:
        yield connexion


def base_est_prete(chemin_base: Path = DB_PATH) -> bool:
    """Indique si la base existe et contient une table `cleaned` non vide."""
    if not chemin_base.is_file():
        return False
    try:
        with ouvrir_connexion(chemin_base) as connexion:
            nombre = connexion.execute(
                f"SELECT COUNT(*) FROM {TABLE_CLEANED}"
            ).fetchone()[0]
    except sqlite3.Error:
        return False
    return nombre > 0


def creer_archive(
    chemin_base: Path = DB_PATH,
    chemin_archive: Path = DB_ARCHIVE_PATH,
) -> None:
    """Compresse les tables `raw` et `cleaned` (format xz) pour Git.

    On travaille sur une copie temporaire : les autres tables éventuellement
    présentes dans la base locale (anciens imports) ne sont ni supprimées
    de la base, ni placées dans l'archive.
    """
    copie = chemin_archive.with_name("archive_temporaire.sqlite")
    copie.unlink(missing_ok=True)
    with closing(sqlite3.connect(chemin_base)) as connexion:
        connexion.execute("VACUUM INTO ?", (str(copie),))
    with closing(sqlite3.connect(copie)) as connexion:
        tables = [
            ligne[0]
            for ligne in connexion.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        ]
        for table in tables:
            if table not in TABLES_ARCHIVEES:
                connexion.execute(f'DROP TABLE "{table}"')
        connexion.commit()
        connexion.execute("VACUUM")
    with copie.open("rb") as source, lzma.open(
        chemin_archive, "wb", preset=6
    ) as cible:
        shutil.copyfileobj(source, cible, length=1024 * 1024)
    copie.unlink()


def restaurer_archive(
    chemin_archive: Path = DB_ARCHIVE_PATH,
    chemin_base: Path = DB_PATH,
) -> bool:
    """Décompresse l'archive versionnée ; retourne False si elle est absente.

    Ne remplace jamais une base existante (règle : aucune suppression de
    données sans validation explicite).

    La base est d'abord écrite dans un fichier temporaire : une interruption
    ne laisse donc jamais une base à moitié écrite.
    """
    if not chemin_archive.is_file() or chemin_base.exists():
        return False
    temporaire = chemin_base.with_suffix(".tmp")
    with lzma.open(chemin_archive, "rb") as source, temporaire.open(
        "wb"
    ) as cible:
        shutil.copyfileobj(source, cible, length=1024 * 1024)
    temporaire.replace(chemin_base)
    return True
