from .all_db import legend_db

def get_players_balance():
    return legend_db.get_key("PLAYERS_BALANCE") or {}


def add_players_balance(user_id, balance):
    ok = get_players_balance()
    ok[user_id] = balance
    return legend_db.set_key("PLAYERS_BALANCE", ok)

