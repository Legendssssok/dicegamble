from .all_db import legend_db


def get_btc_store():
    return legend_db.get_key("BTC_STORE") or {}


def remove_btc_store(user_id):
    ok = get_btc_store()
    ok.pop(user_id)
    return legend_db.set_key("BTC_STORE", ok)


def add_btc_store(
    user_id,
    transaction_amount,
    transaction_address,
    transaction_timeout,
    transaction_checkout_url,
    transaction_qrcode_url,
    transaction_id,
    time,
):
    ok = get_btc_store()
    ok[user_id] = [
        transaction_amount,
        transaction_address,
        transaction_timeout,
        transaction_checkout_url,
        transaction_qrcode_url,
        transaction_id,
        time,
    ]
    return legend_db.set_key("BTC_STORE", ok)
