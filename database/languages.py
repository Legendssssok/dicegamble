from .all_db import legend_db

def all_user_lang():
  return legend_db.get_key("LANGUAGE") or {}
  
def get_user_lang(user_id):
  ok = all_user_lang()
  if user_id in get_user_lang:
    return ok[user_id]

def set_user_lang(user_id, lang_code):
  ok = all_user_lang()
  ok.update({user_id: lang_code})
  return legend_db.set_key("LANGUAGE", ok)

