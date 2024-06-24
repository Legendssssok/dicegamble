from .all_db import legend_db


def get_player_turn():
    return legend_db.get_key("PLAYER") or {}


def add_player_turn(player1, player2):
    ok = get_player_turn()
    ok[player1] = player2
    return legend_db.set_key("PLAYER", ok)


def remove_player_turn(user_id):
    ok = get_player_turn()
    ok.pop(user_id)
    return legend_db.set_key("PLAYER", ok)
