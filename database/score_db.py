from .all_db import legend_db


def get_all_score():
    return legend_db.get_key("SCORE") or {}


def add_score(user_id, player1, player2):
    ok = get_all_score()
    ok[user_id] = [player1, player2]
    return legend_db.set_key("SCORE", ok)
