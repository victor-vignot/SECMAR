"""Tests du contrôle des positions (`src/utils/geographie.py`)."""

import json

import numpy as np
import shapely

from src.utils.geographie import charger_terres, positions_a_terre

# Île fictive carrée de 2° de côté, centrée sur (lat 46, lon 0).
ILE = shapely.box(-1, 45, 1, 47)


def test_point_central_a_terre() -> None:
    """Le centre de l'île est à environ 70 km de la côte : il est repéré."""
    resultat = positions_a_terre(np.array([46.0]), np.array([0.0]), ILE, 5)
    assert resultat.tolist() == [True]


def test_point_pres_de_la_cote_ou_en_mer() -> None:
    """Un point à terre près de la côte, ou en mer, n'est pas repéré."""
    latitudes = np.array([46.0, 46.0])
    longitudes = np.array([0.99, 3.0])  # à ~1 km du bord ; en mer
    assert positions_a_terre(latitudes, longitudes, ILE, 5).tolist() == [False, False]


def test_positions_manquantes() -> None:
    """Une position manquante n'est jamais repérée."""
    resultat = positions_a_terre(np.array([np.nan]), np.array([np.nan]), ILE, 5)
    assert resultat.tolist() == [False]


def test_chargement_geojson(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Un fichier GeoJSON de terres est chargé en une seule géométrie."""
    chemin = tmp_path / "terres.geojson"
    entite = {"type": "Feature", "properties": {}, "geometry": shapely.geometry.mapping(ILE)}
    chemin.write_text(json.dumps({"type": "FeatureCollection", "features": [entite]}))
    terres = charger_terres(chemin)
    assert terres.contains(shapely.Point(0, 46))
