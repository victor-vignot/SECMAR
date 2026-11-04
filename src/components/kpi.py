"""Composant réutilisable pour afficher un indicateur clé (KPI).

L'apparence (couleurs, tailles) est définie dans `assets/style.css` : le
paramètre `ton` choisit la classe CSS de la valeur.
"""

from dash import html

# Tons disponibles, chacun associé à une classe CSS `kpi-valeur--<ton>`.
TONS = ("principal", "secondaire", "alerte", "grave")


def creer_carte_kpi(titre: str, identifiant: str, description: str, ton: str) -> html.Div:
    """Crée une carte KPI : titre, valeur (mise à jour par callback), description."""
    if ton not in TONS:
        raise ValueError(f"Ton inconnu : {ton!r} (attendu : {', '.join(TONS)})")
    return html.Div(
        className=f"kpi kpi--{ton}",
        children=[
            html.P(titre, className="kpi-titre"),
            html.P("—", id=identifiant, className=f"kpi-valeur kpi-valeur--{ton}"),
            html.P(description, className="kpi-description"),
        ],
    )


def formater_nombre(valeur: float | None) -> str:
    """Formate un total avec une espace comme séparateur de milliers."""
    if valeur is None:
        return "N/D"
    return f"{valeur:,.0f}".replace(",", " ")


def formater_duree(heures: float | None) -> str:
    """Formate une durée en heures sous la forme « 1 h 45 min »."""
    if heures is None:
        return "N/D"
    total_minutes = round(heures * 60)
    nombre_heures, minutes = divmod(total_minutes, 60)
    return f"{nombre_heures} h {minutes:02d} min"
