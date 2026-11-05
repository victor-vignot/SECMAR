"""Point d'entrée de l'application SECMAR : `uv run python main.py`."""

import logging

from dash import Dash

from config import DB_ARCHIVE_PATH, DB_PATH
from src.utils.database import base_est_prete, restaurer_archive


def configurer_console() -> None:
    """Garde une console lisible au lancement.

    Le serveur de développement (Werkzeug) affiche un avertissement et une
    ligne par requête : on ne garde que ses erreurs. L'adresse du tableau de
    bord reste affichée par Dash.
    """
    logging.getLogger("werkzeug").setLevel(logging.ERROR)


def preparer_base() -> None:
    """S'assure que la base SQLite est prête avant de construire la page.

    1. Base déjà prête : rien à faire.
    2. Base absente : décompression de l'archive versionnée (sans internet).
    3. Archive absente : téléchargement des CSV puis nettoyage.
    Une base existante sans table `cleaned` n'est jamais écrasée.
    """
    if base_est_prete():
        return
    if DB_PATH.exists():
        raise SystemExit(
            f"{DB_PATH} existe mais ne contient pas la table 'cleaned'.\n"
            "Lancer : uv run python -m src.utils.clean_data"
        )
    print(f"Première exécution : décompression de {DB_ARCHIVE_PATH.name}...")
    if restaurer_archive():
        return
    print("Archive absente : téléchargement et nettoyage des données...")
    # Imports locaux : ces modules ne servent qu'à la reconstruction.
    from src.utils import clean_data, get_data  # pylint: disable=import-outside-toplevel

    get_data.main()
    clean_data.main()


def creer_application() -> Dash:
    """Crée l'application Dash, sa page et ses interactions."""
    # Import après la préparation de la base : la page lit la base.
    from src.pages.dashboard import (  # pylint: disable=import-outside-toplevel
        creer_page_dashboard,
        enregistrer_callbacks,
    )

    app = Dash(__name__, title="SECMAR — Tableau de bord")
    app.layout = creer_page_dashboard()
    enregistrer_callbacks(app)
    return app


if __name__ == "__main__":
    configurer_console()
    preparer_base()
    creer_application().run(debug=False)
