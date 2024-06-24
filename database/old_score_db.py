from .all_db import legend_db


def get_old_score():
    return legend_db.get_key("OLD_SCORE") or {}


def remove_old_score(user_id):
    ok = get_old_score()
    ok.pop(user_id)
    return legend_db.set_key("OLD_SCORE", ok)


def add_old_score(user_id, score):
    ok = get_old_score()
    ok[user_id] = score
    return legend_db.set_key("OLD_SCORE", ok)
