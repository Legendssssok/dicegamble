# from helpers.function import crypto_client

# params = {
#     "cmd": "convert_limits",
#     "from": "USDT.TRC20",
#     "to": "LTC"
# }

# transactioninfo = crypto_client.convert_limit_Coins(params)

# print(transactioninfo)


ok = {}

ok[1] = [1, 2, 3]

print(ok)

lol, hello, fine = ok[1]

print(lol, hello, fine)

ok[1].append(4)

print(ok)

try:
    lol, hello, fine = ok[1]
except:
    lol, hello, fine, text = ok[1]
