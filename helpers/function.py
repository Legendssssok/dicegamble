from pyCoinPayments import CryptoPayments

api_key = "rzp_live_OH4h4RtCPQFnLG"
api_secret = "CPEWuysDiY69CIdZeDwazbdi"

API_KEY = "ff099030be0da6e096dfd3c3f2de3fbdfaf6c68fe07b16fde847705ad9cf9385"
API_SECRET = "7488ea83203cdBcA68ACA88301A77cF775Bf23B549f49f0921a600dDdc437848"
IPN_URL = "https://google.com/ipn"

crypto_client = CryptoPayments(API_KEY, API_SECRET, IPN_URL)


def conversion(convert_1, convert_2, amount):
    params = {"cmd": "rates", "accepted": 1}
    rate = crypto_client.rates(params)
    from_rate = rate[convert_1]["rate_btc"]
    to_rate = rate[convert_2]["rate_btc"]
    conversion_rate = float(from_rate) / float(to_rate)
    new_currency_balance = str(conversion_rate * float(amount))[:10]
    return float(new_currency_balance)
