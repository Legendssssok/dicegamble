from .all_db import legend_db

def get_with_ltc_store():
    return legend_db.get_key("WITH_LTC_STORE") or {}


def remove_with_ltc_store(user_id):
    ok = get_with_ltc_store()
    ok.pop(user_id)
    return legend_db.set_key("WITH_LTC_STORE", ok)

def add_with_ltc_store(user_id, transaction_amount, transaction_id):
    ok = get_with_ltc_store()
    ok[user_id] = [transaction_amount, transaction_id]
    return legend_db.set_key("WITH_LTC_STORE", ok)
