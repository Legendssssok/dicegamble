from .all_db import legend_db


def get_eth_store():
    return legend_db.get_key("ETH_STORE") or {}


def remove_eth_store(user_id):
    ok = get_eth_store()
    ok.pop(user_id)
    return legend_db.set_key("ETH_STORE", ok)


def add_eth_store(
    user_id,
    transaction_amount,
    transaction_address,
    transaction_timeout,
    transaction_checkout_url,
    transaction_qrcode_url,
    transaction_id,
    time,
):
    ok = get_eth_store()
    ok[user_id] = [
        transaction_amount,
        transaction_address,
        transaction_timeout,
        transaction_checkout_url,
        transaction_qrcode_url,
        transaction_id,
        time,
    ]
    return legend_db.set_key("ETH_STORE", ok)
