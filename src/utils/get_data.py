#fichier get_data.py
from urllib.request import Request, urlopen

from config import CSV_PATHS, RAW_DATA_DIR

URLS = {
    "operations": "https://www.data.gouv.fr/api/1/datasets/r/fae6bc13-fe4c-4838-b281-b16628b7babe",
    "flotteurs": "https://www.data.gouv.fr/api/1/datasets/r/ae0e17e4-7117-45f0-80c4-b11b38f31c5c",
    "resultats_humain": "https://www.data.gouv.fr/api/1/datasets/r/8eb7f207-1ce5-460c-b941-5f1761a79c46",
    "operations_stats": "https://www.data.gouv.fr/api/1/datasets/r/5d3c65fb-c861-4b22-b8aa-1eab58e3d9db",
}


def download_file(url, destination):
    """Télécharge une ressource sans transformer son contenu."""
    request = Request(url, headers={"User-Agent": "SECMAR-course-project"})

    with urlopen(request, timeout=120) as response:
        with destination.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)


def main():
    """Télécharge les CSV absents du répertoire data/raw/."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    for name, url in URLS.items():
        destination = CSV_PATHS[name]

        if destination.exists():
            print(f"[CONSERVÉ] {destination} existe déjà.")
            continue

        print(f"[TÉLÉCHARGEMENT] {name}...")
        try:
            download_file(url, destination)
        except Exception:
            destination.unlink(missing_ok=True)
            raise

        print(f"[OK] {destination}")


if __name__ == "__main__":
    main()
