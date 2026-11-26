"""Point d'entrée pour le serveur de production (gunicorn)."""

from flask_compress import Compress

from main import creer_application, preparer_base

preparer_base()
app = creer_application()
server = app.server
Compress(server)
