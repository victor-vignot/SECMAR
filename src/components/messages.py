"""Affichage des messages « à retenir » sous forme de cartes."""

from dash import html

from src.utils.messages import Message


def creer_bandeau_messages(messages: list[Message]) -> html.Div | None:
    """Une carte par message ; rien si la sélection ne permet aucun message."""
    if not messages:
        return None
    return html.Div(
        className="messages",
        children=[
            html.Div(
                className=f"message message--{message.ton}",
                children=[
                    html.P(message.titre, className="message-titre"),
                    html.P(message.texte, className="message-texte"),
                ],
            )
            for message in messages
        ],
    )
