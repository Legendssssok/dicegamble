from .all_db import legend_db


def get_usdt_store():
    return legend_db.get_key("USDT") or {}


def remove_usdt_store(user_id):
    ok = get_usdt_store()
    ok.pop(user_id)
    return legend_db.set_key("USDT_STORE", ok)


def add_usdt_store(
    user_id,
    transaction_amount,
    transaction_address,
    transaction_timeout,
    transaction_checkout_url,
    transaction_qrcode_url,
    transaction_id,
    time,
):
    ok = get_usdt_store()
    ok[user_id] = [
        transaction_amount,
        transaction_address,
        transaction_timeout,
        transaction_checkout_url,
        transaction_qrcode_url,
        transaction_id,
        time,
    ]
    return legend_db.set_key("USDT_STORE", ok)
