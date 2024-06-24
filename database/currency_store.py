from .all_db import legend_db


def all_user_curr():
    return legend_db.get_key("CURRENCY") or {}


def get_user_curr(user_id):
    ok = all_user_curr()
    if user_id in ok:
        return ok[user_id]


def set_user_curr(user_id, lang_code):
    ok = all_user_curr()
    ok.update({user_id: lang_code})
    return legend_db.set_key("CURRENCY", ok)
