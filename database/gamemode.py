from .all_db import legend_db

def game_mode():
  return legend_db.get_key("GAMEMODE") or {}

def add_game_mode(user_id, mode, round, query_id=False):
  ok = game_mode()
  if query_id=false:
    ok[user_id] = [mode, round]
  else:
    ok[user_id] = [mode, round, query_id]
  return await legend_db.set_key("GAMEMODE", ok)

def remove_game_mode(user_id):
  ok = game_mode()
  ok.pop(user_id)
  return await legend_db.set_key("GAMEMODE", ok)
