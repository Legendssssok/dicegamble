from .all_db import legend_db


def get_ltc_store():
    return legend_db.get_key("LTC_STORE") or {}


def remove_ltc_store(user_id):
    ok = get_ltc_store()
    ok.pop(user_id)
    return legend_db.set_key("LTC_STORE", ok)


def add_ltc_store(
    user_id,
    transaction_amount,
    transaction_address,
    transaction_timeout,
    transaction_checkout_url,
    transaction_qrcode_url,
    transaction_id,
    time,
):
    ok = get_ltc_store()
    ok[user_id] = [
        transaction_amount,
        transaction_address,
        transaction_timeout,
        transaction_checkout_url,
        transaction_qrcode_url,
        transaction_id,
        time,
    ]
    return legend_db.set_key("LTC_STORE", ok)
