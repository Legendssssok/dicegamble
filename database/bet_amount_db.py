from .all_db import legend_db

def get_bet_amount():
    return legend_db.get_key("BET_AMOUNT") or {}

def add_bet_amount(user_id, amount):
    ok = get_bet_amount()
    ok[user_id, amount]
    return legend_db.set_key("BET_AMOUNT", ok)

