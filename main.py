import asyncio
import random
import re
import string
import time

import requests
from telethon import Button, TelegramClient, events, functions, types
from telethon.tl.types import BotCommand, InputMediaDice

from pyCoinPayments import CryptoPayments

API_ID = 11573285
API_HASH = "f2cc3fdc32197c8fbaae9d0bf69d2033"
TOKEN = "7213709392:AAGXvbg9v_CqtWCrg270pBHT2-qXe2DWWNw"


client = TelegramClient("LegendBoy", API_ID, API_HASH).start(bot_token=TOKEN)

from database.gamemode import *

score = {}

count_round = {}

player_turn = {}

old_score = {}

players_balance = {}

bet_amount = {}

ltc_store = {}

upi_store = {}

game = [
    [
        Button.inline("🎲 Play against friend", data="playagainstf"),
        Button.inline("🎲 Play against bot", data="playagainstb"),
    ],
    [
        Button.inline("💳 Deposit", data="deposit"),
        Button.inline("💸 Withdraw", data="withdraw"),
    ],
]

back_button = [[Button.inline("⬅️ Back", data="home")]]


@client.on(events.NewMessage(pattern="/start"))
async def start(event):
    await event.client.send_message(
        event.chat_id,
        """**👋 Greetings!**

Play dice with your friend or just with the bot!

Rules are simple: first to reach needed points wins.""",
    )
    if event.is_private:
        now_balance = players_balance.get(event.sender_id, 0)
        await event.client.send_message(
            event.chat_id,
            f"""**🏠 Menu**

Your balance: **${now_balance}**""",
            buttons=game,
        )


# ======= Dice ========#


@client.on(events.NewMessage(pattern="/dice"))
async def dice(event):
    if event.is_private:
        return await event.client.send_message(
            event.chat_id,
            """**🎲 Play against friend**

If you want to play with your friend, you can do it in our group - @.""",
            buttons=back_button,
        )
    ok = game_mode()
    if event.sender_id in ok:
        return await event.reply("Your previous game is yet not finished")
    text = event.text.split(" ")
    try:
        bet = float(text[1])
    except:
        return await event.reply(
            """🎲 Play Dice

To play, type the command /dice with the desired bet.

Examples:
/dice 5.50 - to play for $5.50"""
        )
    now_balance = players_balance.get(event.sender_id, 0)
    if now_balance <= bet:
        return await event.reply(
            f"❌ Not enough balance\n\nYour balance: ${now_balance}"
        )
    await event.client.send_message(
        event.chat_id,
        f"🎲 Choose the game mode",
        buttons=[
            [
                Button.inline(
                    "Normal Mode", data=f"normalmode_{event.sender_id}_{bet}"
                ),
            ],
            [
                Button.inline("Double Roll", data="doubleroll"),
            ],
            [
                Button.inline("Crazy Mode", data="crazymode"),
            ],
            [
                Button.inline("ℹ️ Guide", data=f"diceguide_{event.sender_id}_{bet}"),
                Button.inline("❌ Cancel", data=f"cancel_{event.sender_id}"),
            ],
        ],
    )


def point_button(user_id, bet):
    points_button = [
        [
            Button.inline("5 Round", data=f"round_{user_id}_5_{bet}"),
        ],
        [
            Button.inline("3 Round", data=f"round_{user_id}_3_{bet}"),
        ],
        [
            Button.inline("1 Round", data=f"round_{user_id}_1_{bet}"),
        ],
    ]
    return points_button


def confirm_button(user_id, round, bet):
    confirms_button = [
        [
            Button.inline("✅ Confirm", data=f"confirm_{user_id}_{round}_{bet}"),
            Button.inline("❌ Cancel", data=f"cancel_{user_id}"),
        ]
    ]
    return confirms_button


def final_confirm_button(user_id, round, bet):
    final_confirms_button = [
        [
            Button.inline(
                "✅ Accept Match", data=f"playerwplayer_{user_id}_{round}_{bet}"
            ),
            Button.inline(
                "✅ Play against bot", data=f"botwplayer_{user_id}_{round}_{bet}"
            ),
        ],
        [
            Button.inline("❌ Cancel", data=f"cancel_{user_id}"),
        ],
    ]
    return final_confirms_button


@client.on(events.CallbackQuery)
async def callback_query(event):
    query = event.data.decode("ascii").lower()
    query_user_id = event.query.user_id
    if query.startswith("cancel"):
        user_id = query.split("_")[1]
        if query_user_id != int(user_id):
            return await event.answer(
                "Sorry, but you are not allowed to click others users button"
            )
        await event.delete()
    elif query.startswith("normalmode"):
        user_id, bet = query.split("_")[1:3]
        if query_user_id != int(user_id):
            return await event.answer(
                "Sorry, but you are not allowed to click others users button"
            )
        button = point_button(user_id, bet)
        await event.edit(
            "🎲 Choose the number of rouns to win",
            buttons=button,
        )
    elif query.startswith("round"):
        user_id, round, bet = query.split("_")[1:4]
        if query_user_id != int(user_id):
            return await event.answer(
                "Sorry, but you are not allowed to click others users button"
            )
        points = {"5": 3, "3": 2, "1": 1}[round]
        await event.edit(
            f"""🎲** Game Confirmation**

Your bet: $ {bet}
Win chance: 50/50
Win multiplier: 1.92x
Mode: First to {points} points
Game mode: Normal Mode""",
            buttons=confirm_button(user_id, round, bet),
        )
    elif query.startswith("confirm"):
        user_id, round, bet = query.split("_")[1:4]
        if query_user_id != int(user_id):
            return await event.answer(
                "Sorry, but you are not allowed to click others users button"
            )
        await event.delete()
        user = await client.get_entity(int(user_id))
        points = {"5": 3, "3": 2, "1": 1}[round]
        await event.client.send_message(
            event.chat_id,
            f"""{user.first_name} wants to play dice!

Bet: ${bet}
Win chance: 50/50
Win multiplier: 1.92x
Mode: First to {points} points

Normal Mode
Basic game mode. You take turns rolling the dice, and whoever has the highest digit wins the round.

If you want to play, click the "Accept Match" button""",
            buttons=final_confirm_button(user_id, round, bet),
        )
    elif query.startswith("botwplayer"):
        await asyncio.sleep(1)
        user_id, round, bet = query.split("_")[1:4]
        if query_user_id != int(user_id):
            return await event.answer(
                "Sorry, but you are not allowed to click others users button"
            )
        ok = game_mode()
        if int(user_id) in ok:
            return
        my_bot = await client.get_me()
        user = await client.get_entity(int(user_id))
        now_balance_bot = players_balance.get(my_bot.id, 0)
        if float(now_balance_bot) <= float(bet):
            return await event.answer(
                f"Sorry, ❌ Not enough balance.🏠 Home balance: ${now_balance_bot}"
            )
        left_balance_bot = players_balance[my_bot.id] - float(bet)
        bet_amount[my_bot.id] = float(bet)
        players_balance[my_bot.id] = left_balance_bot
        left_balance_user = players_balance[user.id] - float(bet)
        bet_amount[user.id] = float(bet)
        players_balance[user.id] = left_balance_user
        await event.delete()
        add_game_mode(user.id, "botwplayers", int(round))
        score[user.id] = [0, 0]
        count_round[user.id] = 1
        await event.client.send_message(
            event.chat_id,
            f"""**🎲 Play with Bot**

Player 1: [{user.first_name}](tg://user?id={user.id})
Player 2: [{my_bot.first_name}](tg://user?id={my_bot.id})

**{user.first_name}** , your turn! To start, send a dice emoji: 🎲""",
        )
    elif query.startswith("playerwplayer"):
        user_id, round, bet = query.split("_")[1:4]
        if query_user_id == int(user_id):
            return await event.answer("You cannot accept your own match")
        player1 = await client.get_entity(int(user_id))
        player2 = await client.get_entity(query_user_id)
        now_balance_player2 = players_balance.get(player2.id, 0)
        if float(now_balance_player2) <= float(bet):
            return await event.answer(
                f"❌ Not enough balance. Your balance : ${now_balance_player2}"
            )
        left_balance_player1 = players_balance[player1.id] - float(bet)
        bet_amount[player1.id] = float(bet)
        players_balance[player1.id] = left_balance_player1
        left_balance_player2 = players_balance[player2.id] - float(bet)
        bet_amount[player2.id] = float(bet)
        players_balance[player2.id] = left_balance_player2
        await event.delete()
        score[player1.id] = [0, 0]
        add_game_mode(int(user_id), "playerwplayer", int(round), query_user_id)
        add_game_mode(query_user_id, "playerwplayer", int(round), int(user_id))
        count_round[player1.id] = 1
        player_turn[player1.id] = player1.id
        player_turn[player2.id] = player1.id
        await event.client.send_message(
            event.chat_id,
            f"""**🎲 Player vs Player**

Player 1: [{player1.first_name}](tg://user?id={player1.id})
Player 2: [{player2.first_name}](tg://user?id={player2.id})

**{player1.first_name}** , your turn! To start, send a dice emoji: 🎲""",
        )


@client.on(events.callbackquery.CallbackQuery(data=re.compile(b"back_")))
async def bck_in_groups(event):
    query = event.data.decode("ascii").lower()
    user_id, bet = query.split("_")[1:3]
    query_user_id = event.query.user_id
    if query_user_id != int(user_id):
        return await event.answer(
            "Sorry, but you are not allowed to click others users button"
        )
    await event.edit(
        f"🎲 Choose the game mode",
        buttons=[
            [
                Button.inline("Normal Mode", data=f"normalmode_{user_id}_{bet}"),
            ],
            [
                Button.inline("Double Roll", data="doubleroll"),
            ],
            [
                Button.inline("Crazy Mode", data="crazymode"),
            ],
            [
                Button.inline("ℹ️ Guide", data=f"diceguide_{user_id}_{bet}"),
                Button.inline("❌ Cancel", data=f"cancel_{event.sender_id}"),
            ],
        ],
    )


def back_groups(user_id, bet):
    back_group = [[Button.inline("⬅️ Back", data=f"back_{user_id}_{bet}")]]
    return back_group


@client.on(events.callbackquery.CallbackQuery(data=re.compile(b"diceguide_")))
async def diceguide(event):
    query = event.data.decode("ascii").lower()
    user_id, bet = query.split("_")[1:3]
    query_user_id = event.query.user_id
    if query_user_id != int(user_id):
        return await event.answer(
            "Sorry, but you are not allowed to click others users button"
        )
    await event.edit(
        """🎲 **Game Modes**

**Normal Mode**
Basic game mode. You take turns rolling the dice, and whoever has the highest digit wins the round.

**Double Roll**
Similar to Normal, but you are rolling 2 dice in a row. The winner of the round is the one who has the greater sum of the two dice's digits.

**Crazy Mode**
Are you rolling low all night? Then this Crazy Mode is for you! In this gamemode its all about rolling low! All dices are inverted - 6 is 1 and 1 is 6. Will you be able to keep from going crazy?""",
        buttons=back_groups(user_id, bet),
    )


@client.on(events.callbackquery.CallbackQuery(data=re.compile(b"home")))
async def home(event):
    if event.is_private:
        now_balance = players_balance.get(event.sender_id, 0)
        await event.edit(
            f"""**🏠 Menu**

Your balances: **${now_balance}**""",
            buttons=game,
        )


@client.on(events.callbackquery.CallbackQuery(data=re.compile(b"playagainstf")))
async def playagainstf(event):
    if event.is_private:
        return await event.edit(
            """**🎲 Play against friend**

If you want to play with a bot, use the /dice command in our group - @ None""",
            buttons=back_button,
        )


@client.on(events.callbackquery.CallbackQuery(data=re.compile(b"playagainstb")))
async def playagainstb(event):
    if event.is_private:
        return await event.edit(
            """**🎲 Play against bot**

If you want to play with a bot, use the /dice command in our group - @ None""",
            buttons=back_button,
        )


last_message_times = {}


@client.on(events.NewMessage(incoming=True))
async def gameplay(event):
    ok = game_mode()
    if not event.sender_id in ok:
        return
    if not event.dice:
        return
    lol = event.dice.emoticon == "🎲"
    if not lol:
        return
    if event.sender_id in last_message_times:
        max_time = 9
        time_since_last_message = time.time() - last_message_times[event.sender_id]
        if time_since_last_message < int(max_time):
            return
    my_bot = await client.get_me()
    user = await client.get_entity(event.sender_id)
    gamemode, round = ok[event.sender_id][:2]
    if gamemode == "botwplayers":
        score_player1, score_player2 = score[event.sender_id]
        current_round = count_round[event.sender_id]
        last_message_times[event.sender_id] = time.time()
        player1 = event.media.value
        await asyncio.sleep(3)
        await event.reply("Now it's my turn")
        bot_player = await event.reply(file=InputMediaDice(emoticon="🎲"))
        await asyncio.sleep(3)
        player2 = bot_player.media.value
        if player1 > player2:
            score_player1 += 1
            score[event.sender_id] = [score_player1, score_player2]
        elif player1 < player2:
            score_player2 += 1
            score[event.sender_id] = [score_player1, score_player2]
        else:
            current_round -= 1
        if round == current_round:
            remove_game_mode(event.sender_id)
            count_round.pop(event.sender_id)
            if score_player1 > score_player2:
                add_balance = players_balance[user.id] + float(
                    bet_amount[user.id] * 1.92
                )
                players_balance[user.id] = add_balance
                winner = f"🎉 Congratulations! {user.first_name}, You won : ${bet_amount[user.id] * 1.92}"
            elif score_player1 < score_player2:
                add_balance = players_balance[my_bot.id] + float(
                    bet_amount[my_bot.id] * 1.92
                )
                players_balance[my_bot.id] = add_balance
                winner = f"🎉 Congratulations! {my_bot.first_name}, Bot Won : ${bet_amount[my_bot.id] * 1.92}"
            await event.client.send_message(
                event.chat_id,
                f"""🏆 **Game over!**

**Score:**
{user.first_name} • {score_player1}
{my_bot.first_name} • {score_player2}

{winner}""",
            )
            return
        await event.respond(
            f"""**Score**

{user.first_name}: {score_player1}
{my_bot.first_name}: {score_player2}

[{user.first_name}](tg://user?id={user.id}), it's your turn!""",
        )
        count_round[event.sender_id] = current_round + 1
    elif gamemode == "playerwplayer":
        if player_turn[event.sender_id] != event.sender_id:
            return await event.reply("It's not your turn")
        last_message_times[event.sender_id] = time.time()
        player1 = event.media.value
        player1_details = await client.get_entity(event.sender_id)
        opponent_id = ok[event.sender_id][2]
        player2 = await client.get_entity(opponent_id)
        player_turn[event.sender_id] = player2.id
        player_turn[opponent_id] = player2.id
        await asyncio.sleep(3)
        if count_round.get(player2.id, 1) % 2 == 0:
            current_round = count_round[player2.id]
            score_player1, score_player2 = score[player2.id]
            player1_score = old_score[event.sender_id][0]
            player2_score = player1
            if player1_score > player2_score:
                score_player1 += 1
                score[player2.id] = [score_player1, score_player2]
            elif player1_score < player2_score:
                score_player2 += 1
                score[player2.id] = [score_player1, score_player2]
            else:
                current_round -= 2
            if round + round == current_round:
                remove_game_mode(player2.id)
                remove_game_mode(player1_details.id)
                count_round.pop(player2.id)
                player_turn.pop(player2.id)
                player_turn.pop(player1_details.id)
                old_score.pop(player1_details.id)
                if score_player1 > score_player2:
                    add_balance = players_balance[player2.id] + float(
                        bet_amount[player2.id] * 1.92
                    )
                    players_balance[player2.id] = add_balance
                    winner = f"🎉 Congratulations! {player2.first_name}, You won : ${bet_amount[player2.id] * 1.92}"
                elif score_player1 < score_player2:
                    add_balance = players_balance[player1_details.id] + float(
                        bet_amount[player1_details.id] * 1.92
                    )
                    players_balance[player1_details.id] = add_balance
                    winner = f"🎉 Congratulations! {player1_details.first_name}, You won : ${bet_amount[player1_details.id] * 1.92}"
                return await event.client.send_message(
                    event.chat_id,
                    f"""🏆 **Game over!**

**Score:**
{player2.first_name}  • {score_player1}
{player1_details.first_name}• {score_player2}

{winner}""",
                )
            await event.reply(
                f"""**Score**

{player2.first_name}: {score_player1}
{player1_details.first_name}: {score_player2}

[{player2.first_name}](tg://user?id={player2.id}), it's your turn!"""
            )
            count_round[player2.id] = current_round + 1
        else:
            current_round = count_round[event.sender_id]
            old_score[player2.id] = [player1]
            await event.reply(
                f"[{player2.first_name}](tg://user?id={player2.id}) your turn"
            )
            count_round[event.sender_id] = current_round + 1


# ============ balance, deposit, withdrawal =========#


api_key = "rzp_live_OH4h4RtCPQFnLG"
api_secret = "CPEWuysDiY69CIdZeDwazbdi"

API_KEY = "f7d33ea12c30dfdd2df8bb63f521145b24108416ec8ff05e3292b90cb69e5ba6"
API_SECRET = "1Cc25057C77617495dB8Ec7448463c3c435409Bd46c5F03EEaDA15f68e77bc7c"
IPN_URL = "https://google.com/ipn"

crypto_client = CryptoPayments(API_KEY, API_SECRET, IPN_URL)


@client.on(events.NewMessage(pattern="/housebal"))
async def house_bal(event):
    my_bot = await client.get_me()
    now_balance = players_balance.get(my_bot.id, 0)
    await event.reply(
        f"💰** House Balance**\n\nAvailable balance of the bot: ${now_balance}"
    )


@client.on(events.NewMessage(pattern="/addhousebal"))
async def house_bal(event):
    amount = event.text.split(" ")[1]
    my_bot = await client.get_me()
    old_balance = players_balance.get(my_bot.id, 0)
    now_balance = float(old_balance) + float(amount)
    players_balance[my_bot.id] = now_balance
    await event.reply(
        f"💰** House Balance**\n\nAvailable balance of the bot: ${now_balance}"
    )


@client.on(events.NewMessage(pattern="/bal"))
async def balance_func(event):
    my_bot = await client.get_me()
    balance = players_balance.get(event.sender_id, 0)
    if event.is_private:
        await event.reply(
            f"Your balance:** ${balance}**",
            buttons=[
                [
                    Button.inline("💳 Deposit", data="deposit"),
                    Button.inline("💸 Withdraw", data="withdraw"),
                ]
            ],
        )
    else:
        await event.reply(
            f"Your balance: **${balance}**",
            buttons=[
                [
                    Button.url("💳 Deposit", url=f"https://t.me/{my_bot.username}"),
                    Button.url("💸 Withdraw", url=f"https://t.me/{my_bot.username}"),
                ]
            ],
        )


deposit_button = [
    [Button.inline("Litecoin", data="add_litecoin")],
    [Button.inline("Etherum", data="add_etherum")],
    [Button.inline("Bitcoin", data="add_bitcoin")],
    [Button.inline("USDT ERC-20", data="add_usdterc20")],
    [Button.inline("Monero", data="add_monero")],
    [Button.inline("UPI", data="add_upi")],
    [Button.inline("🔙 Back", data="home")],
]


@client.on(events.callbackquery.CallbackQuery(data=re.compile(b"deposit")))
async def deposit_func(event):
    await event.edit(
        f"**💳 Deposit**\n\nChoose your preferred deposit method:",
        buttons=deposit_button,
    )


def addy_button(method):
    addy_buttons = [
        [Button.inline("🔙 Back", data=f"deposit")],
        [Button.inline("🔄 Refresh", data=f"refresh_{method}")],
    ]
    return addy_buttons


@client.on(events.callbackquery.CallbackQuery(data=re.compile(b"refresh")))
async def refresh(event):
    query = event.data.decode("ascii").lower()
    addy = query.split("_")[1]
    query_user_id = event.query.user_id
    if addy == "litecoin":
        addy_buttons = addy_button("litecoin")
        (
            transaction_amount,
            transaction_address,
            transaction_timeout,
            transaction_checkout_url,
            transaction_qrcode_url,
            transaction_id,
            main_time,
        ) = ltc_store[query_user_id]
        post_params1 = {
            "txid": transaction_id,
        }
        transactionInfo = crypto_client.getTransactionInfo(post_params1)
        if transactionInfo["error"] == "ok":
            status = transactionInfo["status_text"]
            if status != "Complete":
                time_since_last_message = time.time() - main_time
                if time_since_last_message > int(transaction_timeout):
                    ltc_store.pop(query_user_id)
                    return await event.edit(
                        f"Link get expired exceed over time, click again to generate",
                        buttons=addy_buttons,
                    )
                remaining_time = int(transaction_timeout) - time_since_last_message
                hours = remaining_time // 3600
                remaining_seconds = remaining_time % 3600
                minutes = remaining_seconds // 60
                seconds = remaining_seconds % 60
                await event.edit(
                    f"""**💳 Litecoin deposit**

To top up your balance, transfer the desired amount to this LTC address.

**Please note:**
1. The deposit address is temporary and is only issued for 1 hour.
2. One address accepts only one payment.
3. Don't create new addy if you have created new addy by clicking on deposit again, don't pay on this addy
4. After Payment Click On Refresh


**LTC address** : `{transaction_address}`
**Transaction Amount**: {transaction_amount}
**CheckOut URL** : {transaction_checkout_url}
**Qr Code URL**: {transaction_qrcode_url}
**Transaction ID** : {transaction_id}

**Expire In :** {int(hours)}:{int(minutes)}:{int(seconds)}""",
                    buttons=addy_buttons,
                    link_preview=False,
                )
                return
            received_fund = transactionInfo["receivedf"]
            net_fund = transactionInfo["netf"]
            await event.edit(
                f"Payment Confirmed! • LTC: {received_fund}, $ soon \n**Net Fund** LTC: {net_fund}, $ soon"
            )
            ltc_store.pop(query_user_id)
    elif addy == "upi":
        addy_buttons = addy_button("upi")
        (res_id, res_amount, res_name, res_email, res_short_url) = upi_store[
            query_user_id
        ]
        url = f"https://api.razorpay.com/v1/payment_links/{res_id}"
        auth_header = (api_key, api_secret)
        try:
            response = requests.get(
                url, headers={"content-type": "application/json"}, auth=auth_header
            )
            response_json = response.json()
        except Exception as e:
            return await event.reply(f"Error : {e}")
        status = response_json["status"]
        amount = response_json["amount_paid"]
        if status == "paid":
            actual_amount = str(amount)[:-2]
            cut_2_percent = calculate_2_percent(actual_amount)
            after_cut_2_percent = float(actual_amount) - cut_2_percent
            old_balance = players_balance.get(event.sender_id, 0)
            now_balance = after_cut_2_percent / 87
            players_balance[event.sender_id] = float(old_balance) + float(now_balance)
            await event.reply(
                f"Payment confirmed! Amount ${now_balance}\n\nYour Balance {players_balance[event.sender_id]}"
            )
            upi_store.pop(query_user_id)
        else:
            await event.edit(
                f"""**💳 UPI deposit**

To top up your balance, transfer the desired amount to this link.

**Please note:**
1. After deposit the address click on Refresh button.
2. One links accepts only one payment.


**Invoice ID** : `{res_id}`
**Transaction Amount**: {res_amount}
**Name**: {res_name}
**Email Address** : {res_email}
**CheckOut URL** : {res_short_url}

**Your Status** : {status}""",
                buttons=addy_buttons,
            )


@client.on(events.callbackquery.CallbackQuery(data=re.compile(b"add_")))
async def deposits_addy(event):
    query = event.data.decode("ascii").lower()
    addy = query.split("_")[1]
    query_user_id = event.query.user_id
    if addy == "litecoin":
        addy_buttons = addy_button("litecoin")
        if query_user_id in ltc_store:
            (
                transaction_amount,
                transaction_address,
                transaction_timeout,
                transaction_checkout_url,
                transaction_qrcode_url,
                transaction_id,
                main_time,
            ) = ltc_store[query_user_id]
            time_since_last_message = time.time() - main_time
            if time_since_last_message > int(transaction_timeout):
                ltc_store.pop(query_user_id)
                return await event.edit(
                    f"Link get expired exceed over time, click again to generate",
                    buttons=addy_buttons,
                )
            remaining_time = int(transaction_timeout) - time_since_last_message
            hours = remaining_time // 3600
            remaining_seconds = remaining_time % 3600
            minutes = remaining_seconds // 60
            seconds = remaining_seconds % 60
            await event.edit(
                f"""**💳 Litecoin deposit**

To top up your balance, transfer the desired amount to this LTC address.

**Please note:**
1. The deposit address is temporary and is only issued for 1 hour.
2. One address accepts only one payment.
3. Don't create new addy if you have created new addy by clicking on deposit again, don't pay on this addy
4. After Payment Click On Refresh


**LTC address** : `{transaction_address}`
**Transaction Amount**: {transaction_amount}
**CheckOut URL** : {transaction_checkout_url}
**Qr Code URL**: {transaction_qrcode_url}
**Transaction ID** : {transaction_id}

**Expire In :** {int(hours)}:{int(minutes)}:{int(seconds)}""",
                buttons=addy_buttons,
                link_preview=False,
            )
            return
        await event.delete()
        async with client.conversation(event.chat_id) as x:
            await x.send_message(
                "**To top up your balance**,\nEnter the desired amount in $."
            )
            old_amount = await x.get_response(timeout=1200)
            create_transaction_params = {
                "amount": int(old_amount.text),
                "currency1": "USD",
                "currency2": "LTC",
            }
            transaction = crypto_client.createTransaction(create_transaction_params)
            if transaction["error"] == "ok":
                transaction_amount = transaction["amount"]
                transaction_address = transaction["address"]
                transaction_timeout = transaction["timeout"]
                transaction_checkout_url = transaction["checkout_url"]
                transaction_qrcode_url = transaction["qrcode_url"]
                transaction_id = transaction["txn_id"]
                hours = transaction_timeout // 3600
                remaining_seconds = transaction_timeout % 3600
                minutes = remaining_seconds // 60
                seconds = remaining_seconds % 60
                await event.client.send_message(
                    event.chat_id,
                    f"""**💳 Litecoin deposit**

To top up your balance, transfer the desired amount to this LTC address.

**Please note:**
1. The deposit address is temporary and is only issued for 1 hour.
2. One address accepts only one payment.
3. Don't create new addy if you have created new addy by clicking on deposit again, don't pay on this addy
4. After Payment Click On Refresh


**LTC address** : `{transaction_address}`
**Transaction Amount**: {transaction_amount}
**CheckOut URL** : {transaction_checkout_url}
**Qr Code URL**: {transaction_qrcode_url}
**Transaction ID** : {transaction_id}

**Expire In :** {int(hours)}:{int(minutes)}:{int(seconds)}""",
                    buttons=addy_buttons,
                    link_preview=False,
                )
                ltc_store[query_user_id] = [
                    transaction_amount,
                    transaction_address,
                    transaction_timeout,
                    transaction_checkout_url,
                    transaction_qrcode_url,
                    transaction_id,
                    time.time(),
                ]
    elif addy == "upi":
        addy_buttons = addy_button("upi")
        if query_user_id in upi_store:
            (res_id, res_amount, res_name, res_email, res_short_url) = upi_store[
                query_user_id
            ]
            await event.edit(
                f"""**💳 UPI deposit**

To top up your balance, transfer the desired amount to this link.

**Please note:**
1. After deposit the address click on Refresh button.
2. One links accepts only one payment.


**Invoice ID** : `{res_id}`
**Transaction Amount**: {res_amount}
**Name**: {res_name}
**Email Address** : {res_email}
**CheckOut URL** : {res_short_url}""",
                buttons=addy_buttons,
            )
            return
        await event.delete()
        async with client.conversation(event.chat_id) as x:
            try:
                await x.send_message(
                    "**To top up your balance**,\nEnter the desired amount which you want to add."
                )
                old_amount = await x.get_response(timeout=1200)
                oamount = old_amount.text
                amount = str(oamount) + "00"
                new_amount = int(amount)
                await x.send_message("Send me your real name to create invoice")
                name = await x.get_response(timeout=1200)
                await x.send_message(
                    "Send me the email in which you want to get confirmation payment"
                )
                email = await x.get_response(timeout=1200)
            except Exception as e:
                return await x.send_message(
                    f"Something went wrong, may be that you are too slow to respose\nMistankely write something in chat, input amount only\n\n**Error**: {e}\n\n**Try again later**"
                )
        reference_id = f"TS{amount}" + email.text[0:3] + generate_random_string(5)
        url = "https://api.razorpay.com/v1/payment_links/"
        headers = {"Content-type": "application/json"}
        data = {
            "amount": new_amount,
            "currency": "INR",
            "accept_partial": False,
            "reference_id": reference_id,
            "description": "Payment for Free Lancing",
            "customer": {"name": name.text, "email": email.text},
            "notify": {"email": True},
            "reminder_enable": True,
            "notes": {"policy_name": "Free Lancing Bima"},
            "callback_url": "https://telegram.me/DiceChallengerBot",
            "callback_method": "get",
        }
        try:
            response = requests.post(
                url, headers=headers, json=data, auth=(api_key, api_secret)
            )
            response_json = response.json()
        except Exception as e:
            return await event.client.send_message(event.chat_id, f"Error: {e}")
        res_amount = str(response_json["amount"])[:-2]
        res_short_url = response_json["short_url"]
        res_email = response_json["customer"]["email"]
        res_id = response_json["id"]
        res_name = response_json["customer"]["name"]
        await event.client.send_message(
            event.chat_id,
            f"""**💳 UPI deposit**

To top up your balance, transfer the desired amount to this link.

**Please note:**
1. After deposit the address click on Refresh button.
2. One links accepts only one payment.


**Invoice ID** : `{res_id}`
**Transaction Amount**: {res_amount}
**Name**: {res_name}
**Email Address** : {res_email}
**CheckOut URL** : {res_short_url}""",
            buttons=addy_buttons,
        )
        upi_store[query_user_id] = [
            res_id,
            res_amount,
            res_name,
            res_email,
            res_short_url,
        ]


def generate_random_string(length):
    letters = string.ascii_letters + string.digits
    return "".join(random.choice(letters) for _ in range(length))


def calculate_2_percent(input_value):
    try:
        num_value = float(input_value)
        result = num_value * 0.02
        return result
    except ValueError:
        return "Invalid input. Please provide a valid number."


# =============== set command ==========#

commands = [
    BotCommand("start", "to start the bot"),
    BotCommand("dice", "to start a bet"),
    BotCommand("bal", "to view you balance help - show bot help"),
    BotCommand("help", "how to use the bot"),
    BotCommand("tip", "to tip anoother person"),
    BotCommand("leaderboard", "to see group statstics"),
    BotCommand("raffle", "to see active raffles"),
    BotCommand("matches", "too see match history"),
    BotCommand(
        "predict", "to bet against the house and predict what dice will ne rolled next"
    ),
    BotCommand("housebal", "to see how much is left in the house balance"),
]


@client.on(events.NewMessage(pattern="/setbotcommand"))
async def set_bot_command(event):
    try:
        result = await client(
            functions.bots.SetBotCommandsRequest(
                scope=types.BotCommandScopeDefault(), lang_code="en", commands=commands
            )
        )
        await event.client.send_message(event.chat_id, f"{result}")
    except Exception as e:
        await event.reply(f"Error : {e}")


# ================== Check Payments Automatically ===================#


from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()


async def check_upi_payments():
    for user_id, payment_details in list(upi_store.items()):
        res_id, res_amount, res_name, res_email, res_short_url = payment_details
        url = f"https://api.razorpay.com/v1/payment_links/{res_id}"
        auth_header = (api_key, api_secret)
        try:
            response = requests.get(
                url, headers={"content-type": "application/json"}, auth=auth_header
            )
            response_json = response.json()
        except Exception as e:
            print(f"Error checking UPI payment for user {user_id}: {e}")
            continue
        status = response_json["status"]
        amount = response_json["amount_paid"]
        if status == "paid":
            actual_amount = str(amount)[:-2]
            cut_2_percent = calculate_2_percent(actual_amount)
            after_cut_2_percent = float(actual_amount) - cut_2_percent
            old_balance = players_balance.get(user_id, 0)
            now_balance = after_cut_2_percent / 87
            players_balance[user_id] = float(old_balance) + float(now_balance)
            # Notify user about the balance update
            await client.send_message(
                user_id,
                f"Payment confirmed! Amount ${now_balance}\n\nYour Balance {players_balance[user_id]}",
            )
            upi_store.pop(user_id)


async def check_crypto_payments():
    for user_id, payment_details in list(ltc_store.items()):
        (
            transaction_amount,
            transaction_address,
            transaction_timeout,
            transaction_checkout_url,
            transaction_qrcode_url,
            transaction_id,
            main_time,
        ) = payment_details
        post_params1 = {"txid": transaction_id}
        transactionInfo = crypto_client.getTransactionInfo(post_params1)
        if transactionInfo["error"] == "ok":
            status = transactionInfo["status_text"]
            if status == "Complete":
                received_fund = transactionInfo["receivedf"]
                net_fund = transactionInfo["netf"]
                # Update the user's balance
                old_balance = players_balance.get(user_id, 0)
                new_balance = old_balance + float(received_fund)
                players_balance[user_id] = new_balance
                # Notify user about the balance update
                await client.send_message(
                    user_id,
                    f"Payment Confirmed! • LTC: {received_fund}, $ soon \n**Net Fund** LTC: {net_fund}, $ soon",
                )
                ltc_store.pop(user_id)


scheduler.add_job(check_upi_payments, "interval", minutes=5)
scheduler.add_job(check_crypto_payments, "interval", minutes=5)


# ==================== Start Client ==================#


client.start()
client.run_until_disconnected()
