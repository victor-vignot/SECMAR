# SECMAR — Tableau de bord des opérations de secours en mer

Tableau de bord interactif (Python, Dash, Plotly, pandas, SQLite) consacré aux
opérations de recherche et de sauvetage coordonnées par les CROSS (Centres
régionaux opérationnels de surveillance et de sauvetage), de 1985 à 2025.

Il répond à six questions (quand, dans quelles conditions, avec quelles
conséquences, combien de temps et à quelle distance, où, et comment l'activité
évolue) et, pour chacune, calcule trois messages à retenir qui suivent les
filtres choisis.

![Vue générale du tableau de bord](images/dashboard.png)

---

## User Guide

### Prérequis

- [uv](https://docs.astral.sh/uv/) installé (il installe lui-même Python 3.14 si besoin).
- Environ 500 Mo d'espace disque libre.

### Installation et lancement

```bash
git clone https://git.esiee.fr/vignotv/secmar.git
cd secmar
uv sync
uv run python main.py
```

Ouvrir ensuite <http://127.0.0.1:8050> dans un navigateur.

Au premier lancement, `main.py` décompresse l'archive versionnée
`data/db_initial.sqlite.xz` en `data/db.sqlite` (quelques secondes, **sans
connexion internet**). Si l'archive est absente, les données sont téléchargées
depuis data.gouv.fr puis nettoyées (quelques minutes, connexion requise).

### Mettre à jour les données

```bash
uv run python -m src.utils.get_data      # télécharge les CSV absents de data/raw/
uv run python -m src.utils.clean_data    # reconstruit les tables raw et cleaned + l'archive
uv run python -m src.utils.inspect_data  # rapport d'inspection des CSV (lecture seule)
```

Pour forcer un nouveau téléchargement, supprimer d'abord les CSV de `data/raw/`.

### Utilisation

- **Filtres** (en haut) : période, CROSS, famille d'événements et périmètre
  (tout, métropole, outre-mer). Ils s'appliquent à toute la page.
- **Indicateurs clés** : opérations, personnes secourues, blessées, décédées,
  durée médiane d'une opération.
- **Carte** : chaque point est une opération ; cliquer sur une famille dans la
  légende pour l'afficher ou la masquer.
- **Six onglets d'analyse** : Quand ?, Conditions, Conséquences, Durée et
  distance, Où ?, Évolution. Chaque onglet commence par trois messages à
  retenir, recalculés avec les filtres. Survoler un graphique affiche le
  détail et les effectifs.
- **Bulles animées** (onglet Évolution) : appuyer sur ▶ ou faire glisser le
  curseur des années ; chaque bulle est une famille d'événements.

### Vidéo de démonstration

Lien : _à compléter après mise en ligne de la vidéo (3 minutes maximum)._

---

## Data

| Élément | Détail |
| --- | --- |
| Jeu de données | [Opérations coordonnées par les CROSS](https://www.data.gouv.fr/fr/datasets/operations-coordonnees-par-les-cross/) |
| Producteur | Direction générale des affaires maritimes, de la pêche et de l'aquaculture (DGAMPA) |
| Licence | Licence Ouverte / Open Licence |
| Documentation officielle | <https://mtes-mct.github.io/secmar-documentation/> |
| Fichiers utilisés | `operations.csv`, `operations_stats.csv` (et `flotteurs.csv`, `resultats_humain.csv` téléchargés pour l'inspection) |
| Trait de côte | [Natural Earth, Land 1:10m, v5.1.2](https://www.naturalearthdata.com/downloads/10m-physical-vectors/10m-land/) (domaine public), pour le contrôle des positions |
| Volume | 394 756 opérations, d'août 1984 à juillet 2026 |

Liens de téléchargement (ressources stables data.gouv.fr, utilisées par `get_data.py`) :

- operations : <https://www.data.gouv.fr/api/1/datasets/r/fae6bc13-fe4c-4838-b281-b16628b7babe>
- operations_stats : <https://www.data.gouv.fr/api/1/datasets/r/5d3c65fb-c861-4b22-b8aa-1eab58e3d9db>
- flotteurs : <https://www.data.gouv.fr/api/1/datasets/r/ae0e17e4-7117-45f0-80c4-b11b38f31c5c>
- resultats_humain : <https://www.data.gouv.fr/api/1/datasets/r/8eb7f207-1ce5-460c-b941-5f1761a79c46>
- trait de côte : <https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.2/geojson/ne_10m_land.geojson>

### Stockage

La base `data/db.sqlite` contient deux tables :

- `raw` : colonnes utiles des deux CSV, jointes sur `operation_id`, valeurs inchangées ;
- `cleaned` : données typées et variables calculées.

Une copie compressée (`data/db_initial.sqlite.xz`, environ 20 Mo) est versionnée :
elle permet de lancer l'application sans connexion.

### Nettoyage et variables calculées

| Variable | Construction |
| --- | --- |
| `famille` | Regroupement des 68 types d'événements (`evenement`) en 9 familles stables (`src/utils/familles.py`) |
| `saison` | Hiver (déc.-févr.), printemps, été, automne, à partir du mois |
| `classe_vent`, `classe_mer` | Regroupement des échelles de Beaufort (0-3, 4-5, 6-7, 8+) et de Douglas (0-2, 3, 4, 5+) |
| `duree_heures` | Fin - réception de l'alerte ; durées nulles, négatives ou supérieures à 72 h écartées |
| `gravite` | Aucune victime / blessés / décès ou disparus |
| `zone` | Façade maritime (Manche - mer du Nord, Atlantique, Méditerranée) ou Outre-mer |
| `latitude`, `longitude` | Retirées (opération sans position) si la position est (0, 0) ou à terre à plus de 5 km de la côte (trait de côte Natural Earth) |
| `distance_cote_mn` | Distance fournie par la source, conservée uniquement en métropole et pour les positions valides |
| `est_evacuation` | Événements d'évacuation sanitaire ou médicale |

Corrections de libellés : CROSS « Adge » → « Agde », département « Réunion » → « La Réunion ».

### Limites connues

- **Deux ruptures de saisie**, grisées sur la courbe annuelle :
  - en 2009-2010, les « difficultés de manœuvre » sont remplacées par les
    « avaries du système de propulsion » : une partie des opérations passe de la
    famille « Difficulté de navigation » à « Avarie ou panne » ;
  - en 2019-2021, le passage du logiciel SECMARweb au logiciel SEAMIS rend la
    colonne `categorie_evenement` incomparable dans le temps (les fausses alertes
    y disparaissent), d'où l'usage des familles construites sur `evenement`.
- Vent et mer manquent pour environ 27 à 29 % des opérations, davantage dans les
  années 2000.
- La distance à la côte est aberrante en Polynésie, en Martinique et pour les
  positions (0, 0) : elle n'est utilisée qu'en métropole.
- 44 412 positions de l'ancien système sont situées à terre, à plus de 5 km de la
  côte (positions par défaut : centre d'une commune, bâtiment d'un CROSS) ; avec
  les 3 316 positions (0, 0) et les 54 941 opérations déjà sans position, elles
  portent à 102 669 (26 %) le nombre d'opérations absentes de la carte.
- Les évacuations sanitaires sont presque toutes antérieures à 2021 (ancien système).
- Les données décrivent les opérations déclenchées, pas l'exposition au risque :
  il y a davantage de monde en mer l'été et par beau temps.

---

## Developer Guide

### Architecture

```mermaid
flowchart TD
    subgraph Données
        A[data.gouv.fr] -->|get_data.py| B[data/raw/*.csv]
        B -->|clean_data.py| C[(data/db.sqlite<br/>raw + cleaned)]
        C -->|database.creer_archive| D[data/db_initial.sqlite.xz]
        D -->|main.preparer_base| C
    end
    subgraph Traitements
        C --> E[queries.py<br/>charger_operations + cache]
        E --> F[aggregations.py<br/>profils, taux, quartiles]
        E --> M[messages.py<br/>messages à retenir]
    end
    subgraph Composants
        F --> G[figures_quand.py … figures_evolution.py<br/>une fonction par graphique]
        G --> H[graphiques.py<br/>constructeurs génériques]
        H --> T[theme.py + assets/style.css]
        I[filters.py, kpi.py, carte.py]
    end
    subgraph Pages
        J[onglets.py<br/>registre des six onglets] --> K[dashboard.py<br/>layout + callbacks]
        G --> J
        M --> J
        I --> K
    end
    K --> L[main.py<br/>application Dash]
    P[config.py] -.-> B & C & E & G
```

| Dossier / fichier | Rôle |
| --- | --- |
| `config.py` | Chemins, période, seuils, classes, libellés, ruptures de saisie : toutes les décisions modifiables |
| `main.py` | Prépare la base puis lance l'application Dash |
| `src/utils/get_data.py` | Téléchargement des CSV et du trait de côte |
| `src/utils/clean_data.py` | Construction des tables `raw` et `cleaned` |
| `src/utils/familles.py` | Correspondance événement → famille |
| `src/utils/geographie.py` | Repérage des positions situées dans les terres (shapely) |
| `src/utils/database.py` | Connexion SQLite en lecture seule, archive compressée |
| `src/utils/queries.py` | Requête filtrée unique (avec cache) et indicateurs clés |
| `src/utils/aggregations.py` | Calculs statistiques réutilisables |
| `src/utils/messages.py` | Messages à retenir de chaque onglet, recalculés avec les filtres |
| `src/utils/inspect_data.py` | Rapport d'inspection des CSV (`data/inspection_rapport.txt`) |
| `src/components/graphiques.py` | Constructeurs génériques (carte de chaleur, boîtes, histogramme, courbes, barres) |
| `src/components/figures_*.py` | Les graphiques de chaque onglet |
| `src/components/` (autres) | Filtres, indicateurs, carte, bandeau de messages, thème |
| `src/pages/onglets.py` | Registre des onglets : question, messages et graphiques |
| `src/pages/dashboard.py` | Mise en page et callbacks |
| `assets/style.css` | Apparence de la page (charte « Signalétique portuaire »), chargée automatiquement par Dash |
| `assets/logo.svg`, `assets/fonts/` | Pictogramme (bouée, dessin original) et polices libres embarquées |
| `tests/` | Tests unitaires (pytest), sur un échantillon synthétique de 2 000 opérations |

### Ajouter un graphique

1. Écrire une fonction `figure_xxx(donnees: pd.DataFrame) -> go.Figure` dans le
   fichier `src/components/figures_*.py` de l'onglet voulu, en s'appuyant sur
   `src/utils/aggregations.py` et sur les constructeurs de `graphiques.py`.
   Si la sélection est vide, renvoyer `figure_vide(titre)`.
2. L'ajouter dans `src/pages/onglets.py`, dans la liste `graphiques` de l'onglet :
   `Graphique(module.figure_xxx, pleine_largeur=False, note="...")`.
3. Les tests communs (`tests/test_figures_communes.py`) le vérifient
   automatiquement (titre, axes, données, sélection vide) ; ajouter un test
   propre au graphique si son calcul le justifie.

### Ajouter un onglet (une page d'analyse)

Ajouter une entrée `Onglet("identifiant", "Titre", "Question posée ?", graphiques=[...],
messages=fonction_messages)` à la liste `ONGLETS` de `src/pages/onglets.py`.
Aucun callback à écrire : le callback `afficher_onglet` utilise le registre.

### Ajouter un message à retenir

Dans `src/utils/messages.py`, compléter la fonction `messages_xxx` de l'onglet :
elle renvoie au plus trois `Message(titre, texte, ton)` (ton `info`, `alerte`
ou `grave`). Ne produire un message que si l'effectif dépasse
`EFFECTIF_MINIMAL_MESSAGE`, pour ne pas commenter quelques opérations.

### Ajouter une colonne

1. La calculer dans `nettoyer()` (`src/utils/clean_data.py`).
2. L'ajouter à `COLONNES_DASHBOARD` (`src/utils/queries.py`).
3. Relancer `uv run python -m src.utils.clean_data`.

### Modifier l'apparence

- Couleurs, polices et mise en page de la page : `assets/style.css` (variables CSS en tête de fichier).
- Couleurs des graphiques (familles, gravité, cartes de chaleur, fond de carte) : `src/components/theme.py`.
- Le code des composants n'utilise que des classes CSS : changer de charte ne demande de
  modifier que ces deux fichiers.

### Tests et qualité

```bash
uv run --group dev pytest
uv run --group dev ruff check .
uv run --group dev mypy main.py config.py src tests
uv run --group dev pylint main.py config.py src tests
uv run --group dev radon cc main.py src -a
```

Les outils de développement sont dans le groupe `dev` de `pyproject.toml` : un
simple `uv sync` installe uniquement les dépendances d'exécution. Un
avertissement émis pendant les tests les fait échouer.
