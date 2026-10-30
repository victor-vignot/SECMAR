
"""Point d'entrée de l'application SECMAR."""

from dash import Dash

from src.pages.dashboard import (
    creer_page_dashboard,
    enregistrer_callbacks,
)


# Crée l'application web.
app = Dash(__name__)
app.title = "SECMAR — Tableau de bord"

# Charge la page et active les interactions.
app.layout = creer_page_dashboard()
enregistrer_callbacks(app)


# Lance le serveur local.
if __name__ == "__main__":
    app.run(debug=True)
