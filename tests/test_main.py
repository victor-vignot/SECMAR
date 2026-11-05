"""Tests du point d'entrée (`main.py`)."""

import logging

from main import configurer_console


def test_console_sans_messages_du_serveur() -> None:
    """Seules les erreurs du serveur de développement restent affichées."""
    configurer_console()
    assert logging.getLogger("werkzeug").level == logging.ERROR
