from .all_db import legend_db


def get_count_round():
    return legend_db.get_key("ROUND") or {}


def add_count_round(user_id, round):
    ok = get_count_round()
    ok[user_id] = round
    return legend_db.set_key("ROUND", ok)


def remove_count_round(user_id):
    ok = get_count_round()
    ok.pop(user_id)
    return legend_db.set_key("ROUND", ok)
