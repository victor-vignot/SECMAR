"""Tests du téléchargement des données (`src/utils/get_data.py`)."""

import ssl

from src.utils.get_data import DESTINATIONS, URLS, creer_contexte_ssl


def test_contexte_ssl_verifie_les_certificats() -> None:
    """Les certificats et le nom du serveur sont bien vérifiés."""
    contexte = creer_contexte_ssl()
    assert contexte.verify_mode == ssl.CERT_REQUIRED
    assert contexte.check_hostname


def test_chaque_ressource_a_une_destination() -> None:
    """Chaque adresse téléchargée a un fichier de destination dans data/raw/."""
    assert set(URLS) == set(DESTINATIONS)
    assert all(url.startswith("https://") for url in URLS.values())
