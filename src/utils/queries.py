"""Requêtes SQLite utilisées par le tableau de bord."""

import sqlite3

import pandas as pd

from config import (
    ANNEE_MAX,
    ANNEE_MIN,
    DB_PATH,
    TABLE_OPERATIONS,
    TABLE_OPERATIONS_STATS,
)


# Charge les valeurs disponibles dans les filtres.
def charger_options_filtres():
    with sqlite3.connect(DB_PATH) as connexion:
        zones = pd.read_sql_query(
            f"""
            SELECT DISTINCT cross
            FROM {TABLE_OPERATIONS}
            WHERE cross IS NOT NULL
              AND TRIM(cross) != ''
              AND LOWER(TRIM(cross)) != 'adge'
            ORDER BY cross
            """,
            connexion,
        )["cross"].tolist()

        evenements = pd.read_sql_query(
            f"""
            SELECT DISTINCT categorie_evenement
            FROM {TABLE_OPERATIONS}
            WHERE categorie_evenement IS NOT NULL
              AND TRIM(categorie_evenement) != ''
            ORDER BY categorie_evenement
            """,
            connexion,
        )["categorie_evenement"].tolist()

    return zones, evenements


# Récupère les opérations correspondant aux filtres.
def charger_operations(annee_debut, annee_fin, zone, evenement):
    requete = f"""
        SELECT
            o.operation_id,
            o.cross,
            o.categorie_evenement,
            o.evenement,
            o.latitude,
            o.longitude,
            o.vent_force,
            o.mer_force,
            o.date_heure_reception_alerte,
            o.date_heure_fin_operation,
            s.annee,
            s.nombre_personnes_secourues,
            s.nombre_personnes_blessees,
            s.nombre_personnes_decedees,
            s.nombre_personnes_disparues
        FROM {TABLE_OPERATIONS} AS o
        JOIN {TABLE_OPERATIONS_STATS} AS s
            ON o.operation_id = s.operation_id
        WHERE s.annee BETWEEN ? AND ?
    """

    parametres = [int(annee_debut), int(annee_fin)]

    if zone and zone != "toutes":
        requete += " AND o.cross = ?"
        parametres.append(zone)

    if evenement and evenement != "toutes":
        requete += " AND o.categorie_evenement = ?"
        parametres.append(evenement)

    with sqlite3.connect(DB_PATH) as connexion:
        donnees = pd.read_sql_query(
            requete,
            connexion,
            params=parametres,
        )

    return donnees


# Prépare les données des KPI, graphiques et de la carte.
def charger_donnees_dashboard(
    annee_debut=ANNEE_MIN,
    annee_fin=ANNEE_MAX,
    zone="toutes",
    evenement="toutes",
):
    donnees = charger_operations(
        annee_debut,
        annee_fin,
        zone,
        evenement,
    )

    colonnes_numeriques = [
        "latitude",
        "longitude",
        "vent_force",
        "mer_force",
        "nombre_personnes_secourues",
        "nombre_personnes_blessees",
        "nombre_personnes_decedees",
        "nombre_personnes_disparues",
    ]

    for colonne in colonnes_numeriques:
        donnees[colonne] = pd.to_numeric(
            donnees[colonne],
            errors="coerce",
        )

    debut = pd.to_datetime(
        donnees["date_heure_reception_alerte"],
        errors="coerce",
        utc=True,
    )
    fin = pd.to_datetime(
        donnees["date_heure_fin_operation"],
        errors="coerce",
        utc=True,
    )

    donnees["duree_heures"] = (
        fin - debut
    ).dt.total_seconds() / 3600

    # Classe les opérations selon les conséquences humaines déclarées.
    # Cette classification est un indicateur simple, pas une expertise
    # complète de la gravité de chaque événement.
    donnees["gravite"] = "Aucun blessé, décès ou disparu"

    personnes_blessees = donnees[
        "nombre_personnes_blessees"
    ].fillna(0)

    personnes_decedees = donnees[
        "nombre_personnes_decedees"
    ].fillna(0)

    personnes_disparues = donnees[
        "nombre_personnes_disparues"
    ].fillna(0)

    donnees.loc[
        personnes_blessees.gt(0),
        "gravite",
    ] = "Blessés"

    donnees.loc[
        personnes_decedees.gt(0) | personnes_disparues.gt(0),
        "gravite",
    ] = "Décès ou disparus"

    donnees["gravite"] = pd.Categorical(
        donnees["gravite"],
        categories=[
            "Aucun blessé, décès ou disparu",
            "Blessés",
            "Décès ou disparus",
        ],
        ordered=True,
    )

    return {
        "operations": donnees,
        "annuel": (
            donnees.groupby("annee", as_index=False)
            .agg(nombre_operations=("operation_id", "nunique"))
            .sort_values("annee")
        ),
        "evenements": (
            donnees.groupby("categorie_evenement", dropna=True)
            .agg(nombre_operations=("operation_id", "nunique"))
            .reset_index()
            .sort_values("nombre_operations", ascending=False)
        ),
        "evenements_detailles": (
            donnees.groupby("evenement", dropna=True)
            .agg(nombre_operations=("operation_id", "nunique"))
            .reset_index()
            .sort_values("nombre_operations", ascending=False)
        ),
    }