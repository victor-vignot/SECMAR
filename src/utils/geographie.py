"""Contrôle des positions : repérer les opérations placées dans les terres.

Une partie des positions de l'ancien système de saisie est une position par
défaut (centre d'une commune, d'un département, bâtiment du CROSS). On les
repère en testant chaque point contre le trait de côte Natural Earth
(1:10 000 000, domaine public) : un point à terre et à plus de quelques
kilomètres de la côte ne peut pas être le lieu d'une opération en mer.
"""

import json
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import shape

# Taille des morceaux du trait de côte placés dans l'index spatial.
POINTS_PAR_SEGMENT = 20

# Longueur d'un degré de latitude, en kilomètres.
KM_PAR_DEGRE = 111.0


def charger_terres(chemin: Path) -> shapely.Geometry:
    """Charge les terres émergées depuis un fichier GeoJSON Natural Earth."""
    with chemin.open(encoding="utf-8") as fichier:
        entites = json.load(fichier)["features"]
    terres = shapely.union_all([shape(entite["geometry"]) for entite in entites])
    shapely.prepare(terres)
    return terres


def _index_trait_de_cote(terres: shapely.Geometry) -> shapely.STRtree:
    """Découpe le trait de côte en petits segments indexés (recherche rapide)."""
    segments = []
    for ligne in shapely.get_parts(terres.boundary):
        coordonnees = shapely.get_coordinates(ligne)
        for debut in range(0, len(coordonnees) - 1, POINTS_PAR_SEGMENT):
            morceau = coordonnees[debut:debut + POINTS_PAR_SEGMENT + 1]
            segments.append(shapely.linestrings(morceau))
    return shapely.STRtree(segments)


def positions_a_terre(
    latitude: np.ndarray,
    longitude: np.ndarray,
    terres: shapely.Geometry,
    distance_min_km: float,
) -> np.ndarray:
    """Indique, pour chaque position, si elle est à terre à plus de `distance_min_km`.

    Les positions manquantes (NaN) donnent False. La conversion des degrés en
    kilomètres est approchée (moyenne des échelles en latitude et en
    longitude) : la précision obtenue, de l'ordre du kilomètre, suffit pour
    écarter des points situés à plusieurs kilomètres dans les terres.
    """
    latitude = np.asarray(latitude, dtype=float)
    longitude = np.asarray(longitude, dtype=float)
    resultat = np.zeros(len(latitude), dtype=bool)
    connues = ~(np.isnan(latitude) | np.isnan(longitude))
    a_terre = np.zeros(len(latitude), dtype=bool)
    a_terre[connues] = shapely.contains_xy(terres, longitude[connues], latitude[connues])
    indices = np.flatnonzero(a_terre)
    if indices.size == 0:
        return resultat
    points = shapely.points(longitude[indices], latitude[indices])
    _, distance_degres = _index_trait_de_cote(terres).query_nearest(
        points, return_distance=True, all_matches=False
    )
    echelle = np.sqrt((np.cos(np.radians(latitude[indices])) ** 2 + 1) / 2)
    resultat[indices] = distance_degres * KM_PAR_DEGRE * echelle > distance_min_km
    return resultat
