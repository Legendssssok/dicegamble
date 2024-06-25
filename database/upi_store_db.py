from .all_db import legend_db


def get_upi_store():
    return legend_db.get_key("UPI_STORE") or {}


def remove_upi_store(user_id):
    ok = get_upi_store()
    ok.pop(user_id)
    return legend_db.set_key("UPI_STORE", ok)


def add_upi_store(user_id, res_id, res_amount, res_name, res_email, res_short_url):
    ok = get_upi_store()
    ok[user_id] = [res_id, res_amount, res_name, res_email, res_short_url]
    return legend_db.set_key("UPI_STORE", ok)
