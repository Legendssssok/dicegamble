import asyncio
import random
import re
import string
import time
from decimal import Decimal, getcontext

import requests
from telethon import Button, TelegramClient, events, functions, types
from telethon.tl.types import BotCommand, InputMediaDice

from database.bet_amount_db import add_bet_amount, get_bet_amount
from database.btc_store_db import get_btc_store, remove_btc_store
from database.count_round_db import add_count_round, get_count_round, remove_count_round
from database.currency_store import *
from database.eth_store_db import get_eth_store, remove_eth_store
from database.gamemode import *
from database.languages import set_user_lang
from database.ltc_store_db import add_ltc_store, get_ltc_store, remove_ltc_store
from database.old_score_db import add_old_score, get_old_score, remove_old_score
from database.player_turn_db import add_player_turn, get_player_turn, remove_player_turn
from database.players_balance_db import add_players_balance, get_players_balance
from database.score_db import *
from database.upi_store_db import add_upi_store, get_upi_store, remove_upi_store
from database.usdt_store_db import get_usdt_store, remove_usdt_store
from database.with_ltc_store_db import (
    add_with_ltc_store,
    get_with_ltc_store,
    remove_with_ltc_store,
)
from helpers.function import conversion
from strings import *

getcontext().prec = 8  # Set the precision to 8 decimal places

API_ID = 11573285
API_HASH = "f2cc3fdc32197c8fbaae9d0bf69d2033"
TOKEN = "7213709392:AAGXvbg9v_CqtWCrg270pBHT2-qXe2DWWNw"


client = TelegramClient("LegendBoy", API_ID, API_HASH).start(bot_token=TOKEN)


# ======= Game Function======


def game(user_id):
    games = [
        [
            Button.inline(get_string("game_1", user_id), data="playagainstf"),
            Button.inline(get_string("game_2", user_id), data="playagainstb"),
        ],
        [
            Button.inline(get_string("game_3", user_id), data="deposit"),
            Button.inline(get_string("game_4", user_id), data="withdraw"),
        ],
        [
            Button.inline(get_string("game_5", user_id), data="settings"),
        ],
    ]
    return games


@client.on(events.NewMessage(pattern="/start"))
async def start(event):
    await event.client.send_message(
        event.chat_id, get_string("start_greeting", event.sender_id)
    )
    if event.is_private:
        games = game(event.sender_id)
        players_balance = get_players_balance()
        now_balance = players_balance.get(event.sender_id, 0)  # balance in ltc
        usdt_balance = conversion("LTC", "USDT", now_balance)  # convert balance in usdt
        ur_currency = get_user_curr(event.sender_id) or "LTC"
        if ur_currency == "INR":
            currency_balance = usdt_balance * 87
        else:
            currency_balance = conversion("LTC", ur_currency, now_balance)
        await event.client.send_message(
            event.chat_id,
            get_string(
                "start_greeting2",
                event.sender_id,
                "**🏠 Menu**\n\nYour balance: **${}** ({} {})",
            ).format(str(usdt_balance)[:10], str(currency_balance)[0:8], ur_currency),
            buttons=games,
        )


@client.on(events.callbackquery.CallbackQuery(data=re.compile(b"home")))
async def home(event):
    games = game(event.sender_id)
    if event.is_private:
        players_balance = get_players_balance()
        now_balance = players_balance.get(event.sender_id, 0)  # balance in ltc
        usdt_balance = conversion("LTC", "USDT", now_balance)  # convert balance in usdt
        ur_currency = get_user_curr(event.sender_id) or "LTC"
        if ur_currency == "INR":
            currency_balance = usdt_balance * 87
        else:
            currency_balance = conversion(
                "LTC", ur_currency, now_balance
            )  # convert ltc balance to any currency
        await event.edit(
            get_string(
                "start_greeting2",
                event.sender_id,
                "**🏠 Menu**\n\nYour balance: **${}** ({} {})",
            ).format(str(usdt_balance)[:10], str(currency_balance)[0:8], ur_currency),
            buttons=games,
        )


@client.on(events.callbackquery.CallbackQuery(data=re.compile(b"playagainstf")))
async def playagainstf(event):
    if event.is_private:
        back_buttons = back_button(event.sender_id)
        return await event.edit(
            get_string(
                "start_greeting3",
                event.sender_id,
                """**🎲 Play against friend**

If you want to play with a bot, use the /dice command in our group - @sdicers""",
            ),
            buttons=back_buttons,
        )


@client.on(events.callbackquery.CallbackQuery(data=re.compile(b"playagainstb")))
async def playagainstb(event):
    if event.is_private:
        back_buttons = back_button(event.sender_id)
        return await event.edit(
            get_string(
                "start_greeting4",
                event.sender_id,
                """**🎲 Play against bot**

If you want to play with a bot, use the /dice command in our group - @sdicers""",
            ),
            buttons=back_buttons,
        )


# ========== Settings =========


@client.on(events.callbackquery.CallbackQuery(data=re.compile(b"settings")))
async def settings(event):
    user_id = event.sender_id
    languages = get_languages()
    lang_buttons = [
        Button.inline(lang["name"], f"set_lang_{code}")
        for code, lang in languages.items()
    ]

    # Group buttons into rows of 2
    buttons = [lang_buttons[i : i + 2] for i in range(0, len(lang_buttons), 2)]
    buttons.append(
        [
            Button.inline(
                get_string("change_currency", user_id, "Change your currency"),
                data="change_currency",
            )
        ]
    )
    buttons.append([Button.inline(get_string("back", user_id), data="home")])
    await event.edit(get_string("choose_language", user_id), buttons=buttons)


@client.on(events.CallbackQuery(pattern=b"set_lang_"))
async def callack(event):
    user_id = event.sender_id
    lang_code = event.data.decode("utf-8").split("_")[-1]
    set_user_lang(user_id, lang_code)
    ULTConfig.lang = lang_code
    await event.edit(get_string("language_set", user_id))
    await show_main_menu(event)


async def show_main_menu(event):
    user_id = event.sender_id
    languages = get_languages()
    lang_buttons = [
        Button.inline(lang["name"], f"set_lang_{code}")
        for code, lang in languages.items()
    ]

    # Group buttons into rows of 2
    buttons = [lang_buttons[i : i + 2] for i in range(0, len(lang_buttons), 2)]
    buttons.append([Button.inline(get_string("back", user_id), data="home")])
    await event.edit(get_string("choose_language", user_id), buttons=buttons)


def currency_button(user_id):
    button = [
        [
            Button.inline("Litecoin", data="currency_LTC"),
            Button.inline("Etherum", data="currency_ETH"),
        ],
        [
            Button.inline("INR", data="currency_INR"),
            Button.inline("Usdt", data="currency_USD"),
        ],
        [
            Button.inline(get_string("back", user_id), data="settings"),
        ],
    ]
    return button


@client.on(events.CallbackQuery(pattern=b"change_currency"))
async def change_curenc(event):
    user_id = event.sender_id
    ur_currency = get_user_curr(event.sender_id) or "LTC"
    button = currency_button(user_id)
    await event.edit(
        get_string(
            "choose_currency", user_id, "Currency : {}\n\nChoose your Currency Address"
        ).format(ur_currency),
        buttons=button,
    )


@client.on(events.CallbackQuery(pattern=b"currency_"))
async def callack(event):
    user_id = event.sender_id
    curr_code = event.data.decode("utf-8").split("_")[-1]
    set_user_curr(user_id, curr_code)
    await event.edit(
        get_string("curr_set", user_id, "Successfully changed your currency")
    )
    await show_next_curr_menu(event)


async def show_next_curr_menu(event):
    user_id = event.sender_id
    ur_currency = get_user_curr(event.sender_id) or "LTC"
    button = currency_button(user_id)
    await event.edit(
        get_string(
            "choose_currency", user_id, "Currency : {}\n\nChoose your Currency Address"
        ).format(ur_currency),
        buttons=button,
    )


# ======= Dice ========#


def back_button(user_id):
    back_buttons = [[Button.inline(get_string("home_back", user_id), data="home")]]
    return back_buttons


@client.on(events.NewMessage(pattern="/dice"))
async def dice(event):
    if event.is_private:
        back_buttons = back_button(event.sender_id)
        return await event.client.send_message(
            event.chat_id,
            get_string(
                "dice_1",
                event.sender_id,
                """**🎲 Play against friend**

If you want to play with your friend, you can do it in our group - @.""",
            ),
            buttons=back_buttons,
        )
    ok = game_mode()
    if event.sender_id in ok:
        return await event.reply(
            get_string(
                "dice_2", event.sender_id, "Your previous game is yet not finished"
            )
        )
    text = event.text.split(" ")
    try:
        bet = Decimal(text[1])
    except:
        return await event.reply(
            get_string(
                "dice_3",
                event.sender_id,
                """🎲 Play Dice

To play, type the command /dice with the desired bet.

Examples:
/dice 5.50 - to play for $5.50""",
            )
        )
    players_balance = get_players_balance()
    now_balance = players_balance.get(event.sender_id, 0)  # balance in ltc
    usdt_balance = conversion("LTC", "USDT", now_balance)
    if bet < 0.005:
        return await even.reply(
            "get_string"("extra_dice_4", event.sender_id, "minimum bet $0,005")
        )
    if usdt_balance <= bet:  # all in decimal
        return await event.reply(
            get_string(
                "dice_4",
                event.sender_id,
                "❌ Not enough balance\n\nYour balance: ${} ({} LTC)",
            ).format(usdt_balance, now_balance)
        )
    await event.client.send_message(
        event.chat_id,
        get_string("dice_5", event.sender_id, "🎲 Choose the game mode"),
        buttons=[
            [
                Button.inline(
                    get_string("dice_6", event.sender_id, "Normal Mode"),
                    data=f"normalmode_{event.sender_id}_{bet}",
                ),
            ],
            [
                Button.inline(
                    get_string("dice_7", event.sender_id, "Double Roll"),
                    data="doubleroll",
                ),
            ],
            [
                Button.inline(
                    get_string("dice_8", event.sender_id, "Crazy Mode"),
                    data="crazymode",
                ),
            ],
            [
                Button.inline(
                    get_string("dice_9", event.sender_id, "ℹ️ Guide"),
                    data=f"diceguide_{event.sender_id}_{bet}",
                ),
                Button.inline(
                    get_string("dice_10", event.sender_id, "❌ Cancel"),
                    data=f"cancel_{event.sender_id}",
                ),
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
        [Button.inline("❌ Cancel", data=f"cancel_{user_id}")],
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
        players_balance = get_players_balance()
        now_balance_bot = players_balance.get(my_bot.id, 0)  # balance in ltc
        usdt_now_balance_bot = conversion("LTC", "USDT", now_balance_bot)
        if usdt_now_balance_bot < 0.005:
            return await event.answer("Minimum bet $0.005")
        bet_amount_in_ltc = conversion("USDT", "LTC", bet)  # decimal
        if now_balance_bot <= bet_amount_in_ltc:  # all in decimal
            return await event.answer(
                f"Sorry, ❌ Not enough balance.🏠 Home balance: ${usdt_now_balance_bot} ({now_balance_bot} LTC)"
            )
        left_balance_bot = (
            players_balance[my_bot.id] - bet_amount_in_ltc
        )  # left balance in ltc
        add_bet_amount(my_bot.id, float(bet))  # add bet amount in usdt
        add_players_balance(my_bot.id, left_balance_bot)  # add left balance in ltc
        left_balance_user = (
            players_balance[user.id] - bet_amount_in_ltc
        )  # left balance in ltc
        add_bet_amount(user.id, float(bet))  # add bet amount in usdt
        add_players_balance(user.id, left_balance_user)  # add left balance in ltc
        await event.delete()
        add_game_mode(user.id, "botwplayers", int(round))
        add_score(user.id, 0, 0)
        add_count_round(user.id, 1)
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
        players_balance = get_players_balance()
        now_balance_player2 = players_balance.get(
            player2.id, 0
        )  # available balance of 2nd player in ltc
        conversion("LTC", "USDT", now_balance_player2)
        if bet_amount_in_ltc < 0.005:
            return await event.answer("Minimum bet $0.005")
        bet_amount_in_ltc = conversion("USDT", "LTC", float(bet))  # rreturn in decimal
        if Decimal(now_balance_player2) <= bet_amount_in_ltc:
            return await event.answer(
                f"❌ Not enough balance. Your balance : ({now_balance_player2} LTC)"
            )
        left_balance_player1 = (
            players_balance[player1.id] - bet_amount_in_ltc
        )  # LEFT BALANCE OF PLAYER1 IN LTC
        add_bet_amount(player1.id, float(bet))  # ADD BET OF  PLAYER 1 IN USDT
        add_players_balance(
            player1.id, left_balance_player1
        )  # Add left balance of player 1
        left_balance_player2 = players_balance[player2.id] - bet_amount_in_ltc
        add_bet_amount(player2.id, float(bet))
        add_players_balance(player2.id, left_balance_player2)
        await event.delete()
        add_score(player1.id, 0, 0)
        add_game_mode(int(user_id), "playerwplayer", int(round), query_user_id)
        add_game_mode(query_user_id, "playerwplayer", int(round), int(user_id))
        add_count_round(player1.id, 1)
        add_player_turn(player1.id, player1.id)
        add_player_turn(player2.id, player1, id)
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
        ok = get_all_score()
        score_player1, score_player2 = ok[event.sender_id]
        ok = get_count_round()
        current_round = ok[event.sender_id]
        last_message_times[event.sender_id] = time.time()
        player1 = event.media.value
        await asyncio.sleep(3)
        await event.reply("Now it's my turn")
        bot_player = await event.reply(file=InputMediaDice(emoticon="🎲"))
        await asyncio.sleep(3)
        player2 = bot_player.media.value
        if player1 > player2:
            score_player1 += 1
            add_score(event.sender_id, score_player1, score_player2)
        elif player1 < player2:
            score_player2 += 1
            add_score(event.sender_id, score_player1, score_player2)
        else:
            current_round -= 1
        if round == current_round:
            bet_amount = get_bet_amount()
            players_balance = get_players_balance()
            remove_game_mode(event.sender_id)
            remove_count_round(event.sender_id)
            if score_player1 > score_player2:
                win_amount_in_usdt = bet_amount[user.id] * 1.92  # win amount in usdt
                win_amount_in_ltc = conversion(
                    "USDT", "LTC", win_amount_in_usdt
                )  # convert win amount in ltc to add balance
                add_balance = Decimal(players_balance[user.id]) + Decimal(
                    win_amount_in_ltc
                )
                add_players_balance(user.id, add_balance)
                winner = f"🎉 Congratulations! {user.first_name}, You won : ${win_amount_in_usdt}"
            elif score_player1 < score_player2:
                win_amount_in_usdt = bet_amount[my_bot.id] * 1.92  # win amount in usdt
                win_amount_in_ltc = conversion(
                    "USDT", "LTC", win_amount_in_usdt
                )  # convert win amount in ltc to add balance
                add_balance = float(
                    Decimal(players_balance[my_bot.id]) + Decimal(win_amount_in_ltc)
                )
                add_players_balance(my_bot.id, add_balance)
                winner = f"🎉 Congratulations! {my_bot.first_name}, You won : ${win_amount_in_usdt}"
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
        add_count_round(event.sender_id, current_round + 1)
    elif gamemode == "playerwplayer":
        player_turn = get_player_turn()
        if player_turn[event.sender_id] != event.sender_id:
            return await event.reply("It's not your turn")
        last_message_times[event.sender_id] = time.time()
        player1 = event.media.value
        player1_details = await client.get_entity(event.sender_id)
        opponent_id = ok[event.sender_id][2]
        player2 = await client.get_entity(opponent_id)
        add_player_turn(event.sender_id, player1.id)
        add_player_turn(opponent_id, player1.id)
        await asyncio.sleep(3)
        count_round = get_count_round()
        if count_round.get(player2.id, 1) % 2 == 0:
            current_round = count_round[player2.id]
            ok = get_all_score()
            score_player1, score_player2 = ok[player2.id]
            old_score = get_old_score()
            player1_score = old_score[event.sender_id][0]
            player2_score = player1
            if player1_score > player2_score:
                score_player1 += 1
                add_score(player2.id, score_player1, score_player2)
            elif player1_score < player2_score:
                score_player2 += 1
                add_score(player2.id, score_player1, score_player2)
            else:
                current_round -= 2
            if round + round == current_round:
                remove_game_mode(player2.id)
                remove_game_mode(player1_details.id)
                remove_count_round(player2.id)
                remove_player_turn(player2.id)
                remove_player_turn(player1_details.id)
                remove_old_score(player1_details.id)
                bet_amount = get_bet_amount()
                players_balance = get_players_balance()
                if score_player1 > score_player2:
                    win_amount_in_usdt = (
                        bet_amount[player2.id] * 1.92
                    )  # win amount in usdt
                    win_amount_in_ltc = conversion(
                        "USDT", "LTC", win_amount_in_usdt
                    )  # convert win amount in ltc to add balance
                    add_balance = float(
                        Decimal(players_balance[player2.id])
                        + Decimal(win_amount_in_ltc)
                    )
                    add_players_balance(player2.id, add_balance)
                    winner = f"🎉 Congratulations! {player2.first_name}, You won : ${win_amount_in_usdt}"
                elif score_player1 < score_player2:
                    win_amount_in_usdt = (
                        bet_amount[player1_details.id] * 1.92
                    )  # win amount in usdt
                    win_amount_in_ltc = conversion(
                        "USDT", "LTC", win_amount_in_usdt
                    )  # convert win amount in ltc to add balance
                    add_balance = Decimal(
                        players_balance[player1_details.id]
                    ) + Decimal(win_amount_in_ltc)
                    add_players_balance(player1_details.id, add_balance)
                    winner = f"🎉 Congratulations! {player1_details.first_name}, You won : ${win_amount_in_usdt}"
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
            add_count_round(player2.id, current_round + 1)
        else:
            current_round = count_round[event.sender_id]
            add_old_score(player2.id, player1)
            await event.reply(
                f"[{player2.first_name}](tg://user?id={player2.id}) your turn"
            )
            add_count_round(event.sender_id, current_round + 1)


# ============ balance, deposit, withdrawal =========#


from helpers.function import api_key, api_secret, crypto_client


@client.on(events.NewMessage(pattern="/housebal"))
async def house_bal(event):
    players_balance = get_players_balance()
    my_bot = await client.get_me()
    now_balance = players_balance.get(my_bot.id, 0)  # balance in ltc
    usdt_balance = conversion("LTC", "USDT", now_balance)
    await event.reply(
        f"💰** House Balance**\n\nAvailable balance of the bot: ${usdt_balance} ({now_balance} LTC)"
    )


@client.on(events.NewMessage(pattern="/addhousebal_1"))
async def house_bal(event):
    players_balance = get_players_balance()
    amount = event.text.split(" ")[1]
    add_balance_in_ltc = conversion("USDT", "LTC", amount)  # convert balance in ltc
    my_bot = await client.get_me()
    old_balance = players_balance.get(my_bot.id, 0)  # balance in ltc
    now_balance = float(old_balance + add_balance_in_ltc)  # float
    add_players_balance(my_bot.id, now_balance)
    await event.reply(
        f"💰** House Balance**\n\nAvailable balance of the bot: {now_balance} LTC"
    )


@client.on(events.NewMessage(pattern="/addmybal_1"))
async def add_bal(event):
    players_balance = get_players_balance()
    amount, user_id = event.text.split(" ")[1:3]
    add_balance_in_ltc = conversion("USDT", "LTC", amount)  # convert balance in ltc
    old_balance = players_balance.get(int(user_id), 0)  # BALANCE IN LTC
    now_balance = float(old_balance + Decimal(add_balance_in_ltc))
    add_players_balance(int(user_id), now_balance)
    await event.reply(
        f"💰** My Balance**\n\nAvailable balance of the {user_id}: {now_balance} LTC"
    )


@client.on(events.NewMessage(pattern="/bal"))
async def balance_func(event):
    players_balance = get_players_balance()
    my_bot = await client.get_me()
    balance_in_ltc = players_balance.get(event.sender_id, 0)  # BALANCE IN LTC
    balance_in_usdt = conversion(
        "LTC", "USDT", balance_in_ltc
    )  # CONVERT BALANCE IN USDT
    if event.is_private:
        await event.reply(
            f"Your balance:** ${balance_in_usdt} ({balance_in_ltc} LTC)**",
            buttons=[
                [
                    Button.inline("💳 Deposit", data="deposit"),
                    Button.inline("💸 Withdraw", data="withdraw"),
                ]
            ],
        )
    else:
        await event.reply(
            f"Your balance:** $ {balance_in_usdt} ({balance_in_ltc} LTC)**",
            buttons=[
                [
                    Button.url("💳 Deposit", url=f"https://t.me/{my_bot.username}"),
                    Button.url("💸 Withdraw", url=f"https://t.me/{my_bot.username}"),
                ]
            ],
        )


# ================ Withdrawal ===========#


def withdrawal_button(user_id):
    withdrawal_buttons = [
        [
            Button.inline("Litecoin", data="with_litecoin"),
            Button.inline("UPI", data="with_upi"),
        ],
        [
            Button.inline(get_string("back", user_id), data="home"),
        ],
    ]
    return withdrawal_buttons


@client.on(events.callbackquery.CallbackQuery(data=(b"withdraw")))
async def deposit_func(event):
    withdrawal_buttons = withdrawal_button(event.sender_id)
    await event.edit(
        f"**💳 Withdrawal**\n\nChoose your preferred withdrawal method:",
        buttons=withdrawal_buttons,
    )


def with_button(method):
    with_buttons = [
        [
            Button.inline("⬅️ Back", data=f"withdraw"),
            Button.inline("🔄 Refresh", data=f"with_refresh_{method}"),
        ],
    ]
    return with_buttons


@client.on(events.callbackquery.CallbackQuery(data=re.compile(b"with_refresh_")))
async def with_refresh(event):
    query = event.data.decode("ascii").lower()
    addy = query.split("_")[1]
    query_user_id = event.query.user_id
    with_ltc_store = get_with_ltc_store()
    if addy == "litecoin":
        if query_user_id not in with_ltc_store:
            await event.reply("Your withdrawal is successfully check your wallet")
            return
        with_buttons = with_button("litecoin")
        transaction_amount, transaction_id = with_ltc_store[query_user_id]
        post_params = {
            "cmd": "get_withdrawal_info",
            "id": transaction_id,
        }
        transaction_with_Info = crypto_client.getWithdrawalInfo(post_params)
        if transaction_with_Info["error"] == "ok":
            status = transaction_with_Info["status_text"]
            if status != "Complete":
                await event.edit(
                    f"""**💳 Litecoin withdrawal**

**Please note:**
1. Withdrawal process is turned on it automatically notified you when withdraw complete 
2. Check status by clicking on Refresh Button

**Transaction ID** : `{transaction_id}`
**Transaction Amount** : {transaction_amount}""",
                    buttons=with_buttons,
                    link_preview=False,
                )
            elif status == "Complete":
                net_fund = transaction_with_Info[
                    "amountf"
                ]  # net received balance in ltc
                players_balance = get_players_balance()
                old_balance = players_balance[query_user_id]  # available balance in ltc
                add_players_balance(
                    query_user_id, float(Decimal(old_balance) - Decimal(net_fund))
                )
                await event.reply(
                    f"Payment withdrawal Confirmed! • LTC: {net_fund}, Left Balance: **({players_balance[query_user_id]} LTC)**"
                )
                remove_with_ltc_store(query_user_id)


@client.on(events.callbackquery.CallbackQuery(data=re.compile(b"with_")))
async def with_addy(event):
    query = event.data.decode("ascii").lower()
    addy = query.split("_")[1]
    query_user_id = event.query.user_id
    players_balance = get_players_balance()  # balance in ltc
    if addy == "litecoin":
        with_ltc_store = get_with_ltc_store()
        with_buttons = with_button("litecoin")
        if query_user_id in with_ltc_store:
            (
                transaction_amount,
                transaction_id,
            ) = with_ltc_store[query_user_id]
            await event.edit(
                f"""**💳 Litecoin withdrawal**

**Please note:**
1. Withdrawal process is turned on it automatically notified you when withdraw complete 
2. Check status by clicking on Refresh Button

**Transaction ID** : `{transaction_id}`
**Transaction Amount** : {transaction_amount}""",
                buttons=with_buttons,
                link_preview=False,
            )
            return
        await event.delete()
        async with client.conversation(event.chat_id) as x:
            await x.send_message("**Please send your Litecoin wallet address:**")
            address = await x.get_response(timeout=1200)
            await x.send_message(
                "Send me the desired withdrawal amount in LTC to the chat:"
            )
            with_amount = await x.get_response(timeout=1200)  # with balance in ltc
            now_balance = players_balance.get(event.sender_id, 0)  # balance in ltc
            if float(now_balance) < float(with_amount.text):
                return await event.reply("Not enough balance")
            create_with_transaction_params = {
                "amount": float(with_amount.text),
                "currency": "LTC",
                "address": address.text,
            }
            transaction = crypto_client.createWithdrawal(create_with_transaction_params)
            if transaction["error"] == "ok":
                transaction_id = transaction["id"]
                transaction_amount = transaction["amount"]
                await event.client.send_message(
                    event.chat_id,
                    f"""**💳 Litecoin withdrawal**

**Please note:**
1. Withdrawal process is turned on it automatically notified you when withdraw complete 
2. Check status by clicking on Refresh Button

**Transaction ID** : `{transaction_id}`
**Transaction Amount** : {transaction_amount}""",
                    buttons=with_buttons,
                    link_preview=False,
                )
                add_with_ltc_store(query_user_id, transaction_amount, transaction_id)
            else:
                await event.reply(transaction["error"])


# =============== Deposit history ============== #

deposit_button = [
    [Button.inline("Litecoin", data="add_litecoin")],
    # [Button.inline("Etherum", data="add_etherum")],
    # [Button.inline("Bitcoin", data="add_bitcoin")],
    # [Button.inline("Usdt Tron", data="add_usdt")],
    [Button.inline("UPI", data="add_upi")],
    [Button.inline("⬅️ Back", data="home")],
]


@client.on(events.callbackquery.CallbackQuery(data=re.compile(b"deposit")))
async def deposit_func(event):
    await event.edit(
        f"**💳 Deposit**\n\nChoose your preferred deposit method:",
        buttons=deposit_button,
    )


def addy_button(method):
    addy_buttons = [
        [
            Button.inline("⬅️ Back", data=f"deposit"),
            Button.inline("🔄 Refresh", data=f"refresh_{method}"),
        ],
    ]
    return addy_buttons


addy_back_buttons = [
    [Button.inline("🔙 Back", data=f"deposit")],
]


@client.on(events.callbackquery.CallbackQuery(data=re.compile(b"refresh")))
async def refresh(event):
    query = event.data.decode("ascii").lower()
    addy = query.split("_")[1]
    query_user_id = event.query.user_id
    players_balance = get_players_balance()
    if addy == "litecoin":
        ltc_store = get_ltc_store()
        if query_user_id not in ltc_store:
            del_msg = await event.edit(
                "Payment was received successfully & was added before to your balance or may be the time exceed."
            )
            await asyncio.sleep(10)
            await del_msg.delete()
            return
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
                    remove_ltc_store(query_user_id)
                    return await event.edit(
                        f"Link get expired exceed over time, click again to generate",
                        buttons=addy_back_buttons,
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
            elif status == "Complete":
                net_fund = transactionInfo["netf"]  # received balance in ltc
                now_balance = conversion("LTC", "USDT", net_fund)
                old_balance = players_balance.get(
                    query_user_id, 0
                )  # old balance in ltc
                add_players_balance(
                    query_user_id, float(Decimal(old_balance) + Decimal(net_fund))
                )  # add balance in ltc
                await event.reply(
                    f"Payment Confirmed! • LTC: {net_fund}, Added Balance : ${now_balance}, Balance: **({players_balance[query_user_id]} LTC)**"
                )
                remove_ltc_store(query_user_id)
    #     elif addy == "etherum":
    #         eth_store = get_eth_store()
    #         if query_user_id not in eth_store:
    #             del_msg = await event.edit(
    #                 "Payment was received successfully & was added before to your balance or may be the time exceed."
    #             )
    #             await asyncio.sleep(10)
    #             await del_msg.delete()
    #             return
    #         addy_buttons = addy_button("etherum")
    #         (
    #             transaction_amount,
    #             transaction_address,
    #             transaction_timeout,
    #             transaction_checkout_url,
    #             transaction_qrcode_url,
    #             transaction_id,
    #             main_time,
    #         ) = eth_store[query_user_id]
    #         post_params1 = {
    #             "txid": transaction_id,
    #         }
    #         transactionInfo = crypto_client.getTransactionInfo(post_params1)
    #         if transactionInfo["error"] == "ok":
    #             status = transactionInfo["status_text"]
    #             if status != "Complete":
    #                 time_since_last_message = time.time() - main_time
    #                 if time_since_last_message > int(transaction_timeout):
    #                     remove_eth_store(query_user_id)
    #                     return await event.edit(
    #                         f"Link get expired exceed over time, click again to generate",
    #                         buttons=addy_back_buttons,
    #                     )
    #                 remaining_time = int(transaction_timeout) - time_since_last_message
    #                 hours = remaining_time // 3600
    #                 remaining_seconds = remaining_time % 3600
    #                 minutes = remaining_seconds // 60
    #                 seconds = remaining_seconds % 60
    #                 await event.edit(
    #                     f"""**💳 Etherum deposit**

    # To top up your balance, transfer the desired amount to this ETH address.

    # **Please note:**
    # 1. The deposit address is temporary and is only issued for 1 hour 30 min.
    # 2. One address accepts only one payment.

    # **ETH address** : `{transaction_address}`
    # **Transaction Amount**: {transaction_amount}
    # **CheckOut URL** : {transaction_checkout_url}
    # **Qr Code URL**: {transaction_qrcode_url}
    # **Transaction ID** : {transaction_id}

    # **Expire In :** {int(hours)}:{int(minutes)}:{int(seconds)}""",
    #                     buttons=addy_buttons,
    #                     link_preview=False,
    #                 )
    #                 return
    #             transactionInfo["receivedf"]
    #             net_fund = transactionInfo["netf"]
    #             params = {"cmd": "rates", "accepted": 1}
    #             rate = crypto_client.rates(params)
    #             from_rate = rate["USDT"]["rate_btc"]
    #             to_rate = rate["ETH"]["rate_btc"]
    #             conversion_rate = float(to_rate) / float(from_rate)
    #             old_balance = players_balance.get(query_user_id, 0)
    #             now_balance = str(conversion_rate * float(net_fund))[:10]
    #             add_players_balance(query_user_id, float(old_balance) + float(now_balance))
    #             await event.reply(
    #                 f"Payment Confirmed! • ETH: {net_fund}, Added Balance : ${now_balance}, Balance: **{players_balance[query_user_id]}**"
    #             )
    #             remove_eth_store(query_user_id)
    #     elif addy == "bitcoin":
    #         btc_store = get_btc_store()
    #         if query_user_id not in btc_store:
    #             del_msg = await event.edit(
    #                 "Payment was received successfully & was added before to your balance or may be the time exceed."
    #             )
    #             await asyncio.sleep(10)
    #             await del_msg.delete()
    #             return
    #         addy_buttons = addy_button("etherum")
    #         (
    #             transaction_amount,
    #             transaction_address,
    #             transaction_timeout,
    #             transaction_checkout_url,
    #             transaction_qrcode_url,
    #             transaction_id,
    #             main_time,
    #         ) = btc_store[query_user_id]
    #         post_params1 = {
    #             "txid": transaction_id,
    #         }
    #         transactionInfo = crypto_client.getTransactionInfo(post_params1)
    #         if transactionInfo["error"] == "ok":
    #             status = transactionInfo["status_text"]
    #             if status != "Complete":
    #                 time_since_last_message = time.time() - main_time
    #                 if time_since_last_message > int(transaction_timeout):
    #                     remove_btc_store(query_user_id)
    #                     return await event.edit(
    #                         f"Link get expired exceed over time, click again to generate",
    #                         buttons=addy_back_buttons,
    #                     )
    #                 remaining_time = int(transaction_timeout) - time_since_last_message
    #                 hours = remaining_time // 3600
    #                 remaining_seconds = remaining_time % 3600
    #                 minutes = remaining_seconds // 60
    #                 seconds = remaining_seconds % 60
    #                 await event.edit(
    #                     f"""**💳 Bitcoin deposit**

    # To top up your balance, transfer the desired amount to this ETH address.

    # **Please note:**
    # 1. The deposit address is temporary and is only issued for 1 hour 30 min.
    # 2. One address accepts only one payment.

    # **BTC address** : `{transaction_address}`
    # **Transaction Amount**: {transaction_amount}
    # **CheckOut URL** : {transaction_checkout_url}
    # **Qr Code URL**: {transaction_qrcode_url}
    # **Transaction ID** : {transaction_id}

    # **Expire In :** {int(hours)}:{int(minutes)}:{int(seconds)}""",
    #                     buttons=addy_buttons,
    #                     link_preview=False,
    #                 )
    #                 return
    #             net_fund = transactionInfo["netf"]
    #             params = {"cmd": "rates", "accepted": 1}
    #             rate = crypto_client.rates(params)
    #             from_rate = rate["USDT"]["rate_btc"]
    #             to_rate = rate["BTC"]["rate_btc"]
    #             conversion_rate = float(to_rate) / float(from_rate)
    #             old_balance = players_balance.get(query_user_id, 0)
    #             now_balance = str(conversion_rate * float(net_fund))[:10]
    #             add_players_balance(query_user_id, float(old_balance) + float(now_balance))
    #             await event.reply(
    #                 f"Payment Confirmed! • BTC: {net_fund}, Added Balance : ${now_balance}, Balance: **{players_balance[query_user_id]}**"
    #             )
    #             remove_btc_store(query_user_id)
    #     elif addy == "usdt":
    #         usdt_store = get_usdt_store()
    #         if query_user_id not in usdt_store:
    #             del_msg = await event.edit(
    #                 "Payment was received successfully & was added before to your balance or may be the time exceed."
    #             )
    #             await asyncio.sleep(10)
    #             await del_msg.delete()
    #             return
    #         addy_buttons = addy_button("usdt")
    #         (
    #             transaction_amount,
    #             transaction_address,
    #             transaction_timeout,
    #             transaction_checkout_url,
    #             transaction_qrcode_url,
    #             transaction_id,
    #             main_time,
    #         ) = usdt_store[query_user_id]
    #         post_params1 = {
    #             "txid": transaction_id,
    #         }
    #         transactionInfo = crypto_client.getTransactionInfo(post_params1)
    #         if transactionInfo["error"] == "ok":
    #             status = transactionInfo["status_text"]
    #             if status != "Complete":
    #                 time_since_last_message = time.time() - main_time
    #                 if time_since_last_message > int(transaction_timeout):
    #                     remove_usdt_store(query_user_id)
    #                     return await event.edit(
    #                         f"Link get expired exceed over time, click again to generate",
    #                         buttons=addy_back_buttons,
    #                     )
    #                 remaining_time = int(transaction_timeout) - time_since_last_message
    #                 hours = remaining_time // 3600
    #                 remaining_seconds = remaining_time % 3600
    #                 minutes = remaining_seconds // 60
    #                 seconds = remaining_seconds % 60
    #                 await event.edit(
    #                     f"""**💳 Bitcoin deposit**

    # To top up your balance, transfer the desired amount to this ETH address.

    # **Please note:**
    # 1. The deposit address is temporary and is only issued for 1 hour 30 min.
    # 2. One address accepts only one payment.

    # **BTC address** : `{transaction_address}`
    # **Transaction Amount**: {transaction_amount}
    # **CheckOut URL** : {transaction_checkout_url}
    # **Qr Code URL**: {transaction_qrcode_url}
    # **Transaction ID** : {transaction_id}

    # **Expire In :** {int(hours)}:{int(minutes)}:{int(seconds)}""",
    #                     buttons=addy_buttons,
    #                     link_preview=False,
    #                 )
    #                 return
    #             net_fund = transactionInfo["netf"]
    #             params = {"cmd": "rates", "accepted": 1}
    #             rate = crypto_client.rates(params)
    #             from_rate = rate["USDT"]["rate_btc"]
    #             to_rate = rate["USDT"]["rate_btc"]
    #             conversion_rate = float(to_rate) / float(from_rate)
    #             old_balance = players_balance.get(query_user_id, 0)
    #             now_balance = str(conversion_rate * float(net_fund))[:10]
    #             add_players_balance(query_user_id, float(old_balance) + float(now_balance))
    #             await event.reply(
    #                 f"Payment Confirmed! • USDT: {net_fund}, Added Balance : ${now_balance}, Balance: **{players_balance[query_user_id]}**"
    #             )
    #             remove_usdt_store(query_user_id)
    elif addy == "upi":
        upi_store = get_upi_store()
        if query_user_id not in upi_store:
            del_msg = await event.edit(
                "Payment was received successfully & Added to your balance"
            )
            await asyncio.sleep(5)
            await del_msg.delete()
            return
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
            actual_amount = str(amount)[:-2]  # actual amount  in india rs
            cut_2_percent = calculate_2_percent(actual_amount)
            after_cut_2_percent = (
                float(actual_amount) - cut_2_percent
            )  # cut 2 percent per transaction
            usdt_balance = str(after_cut_2_percent / 87)[
                :10
            ]  # conver new balance in usdt
            ltc_balance = conversion(
                "USDT", "LTC", usdt_balance
            )  # convert new balance in ltc
            old_balance = players_balance.get(query_user_id, 0)  # balance in ltc
            add_players_balance(query_user_id, float(old_balance) + float(ltc_balance))
            await event.reply(
                f"Payment Confirmed! • INR: {after_cut_2_percent}, Added Balance : ${usdt_balance}, Balance: **({players_balance[query_user_id]} LTC)**"
            )
            remove_upi_store(query_user_id)
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
                link_preview=False,
            )


@client.on(events.callbackquery.CallbackQuery(data=re.compile(b"add_")))
async def deposits_addy(event):
    query = event.data.decode("ascii").lower()
    addy = query.split("_")[1]
    query_user_id = event.query.user_id
    if addy == "litecoin":
        ltc_store = get_ltc_store()
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
                remove_ltc_store(query_user_id)
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
3. After Payment Click On Refresh


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
                "**To top up your balance**,\n\nEnter the desired amount in $:"
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
                transaction_timeout = transaction["timeout"] - 60
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
                add_ltc_store(
                    query_user_id,
                    transaction_amount,
                    transaction_address,
                    transaction_timeout,
                    transaction_checkout_url,
                    transaction_qrcode_url,
                    transaction_id,
                    time.time(),
                )
    #     elif addy == "etherum":
    #         eth_store = get_eth_store()
    #         addy_buttons = addy_button("etherum")
    #         if query_user_id in eth_store:
    #             (
    #                 transaction_amount,
    #                 transaction_address,
    #                 transaction_timeout,
    #                 transaction_checkout_url,
    #                 transaction_qrcode_url,
    #                 transaction_id,
    #                 main_time,
    #             ) = eth_store[query_user_id]
    #             time_since_last_message = time.time() - main_time
    #             if time_since_last_message > int(transaction_timeout):
    #                 remove_eth_store(query_user_id)
    #                 return await event.edit(
    #                     f"Link get expired exceed over time, click again to generate",
    #                     buttons=addy_buttons,
    #                 )
    #             remaining_time = int(transaction_timeout) - time_since_last_message
    #             hours = remaining_time // 3600
    #             remaining_seconds = remaining_time % 3600
    #             minutes = remaining_seconds // 60
    #             seconds = remaining_seconds % 60
    #             await event.edit(
    #                 f"""**💳 Etherum deposit**

    # To top up your balance, transfer the desired amount to this ETH address.

    # **Please note:**
    # 1. The deposit address is temporary and is only issued for 1 hour.
    # 2. One address accepts only one payment.

    # **ETH address** : `{transaction_address}`
    # **Transaction Amount**: {transaction_amount}
    # **CheckOut URL** : {transaction_checkout_url}
    # **Qr Code URL**: {transaction_qrcode_url}
    # **Transaction ID** : {transaction_id}

    # **Expire In :** {int(hours)}:{int(minutes)}:{int(seconds)}""",
    #                 buttons=addy_buttons,
    #                 link_preview=False,
    #             )
    #             return
    #         await event.delete()
    #         async with client.conversation(event.chat_id) as x:
    #             await x.send_message(
    #                 "**To top up your balance**\n\n**Please Note**: Minimum deposit $30\n\nEnter the desired $ amount:"
    #             )
    #             old_amount = await x.get_response(timeout=1200)
    #             create_transaction_params = {
    #                 "amount": int(old_amount.text),
    #                 "currency1": "USD",
    #                 "currency2": "ETH",
    #             }
    #             transaction = crypto_client.createTransaction(create_transaction_params)
    #             if transaction["error"] == "ok":
    #                 transaction_amount = transaction["amount"]
    #                 transaction_address = transaction["address"]
    #                 transaction_timeout = transaction["timeout"] - 60
    #                 transaction_checkout_url = transaction["checkout_url"]
    #                 transaction_qrcode_url = transaction["qrcode_url"]
    #                 transaction_id = transaction["txn_id"]
    #                 hours = transaction_timeout // 3600
    #                 remaining_seconds = transaction_timeout % 3600
    #                 minutes = remaining_seconds // 60
    #                 seconds = remaining_seconds % 60
    #                 await event.client.send_message(
    #                     event.chat_id,
    #                     f"""**💳 Etherum deposit**

    # To top up your balance, transfer the desired amount to this LTC address.

    # **Please note:**
    # 1. The deposit address is temporary and is only issued for 1 hour.
    # 2. One address accepts only one payment.

    # **ETH address** : `{transaction_address}`
    # **Transaction Amount**: {transaction_amount}
    # **CheckOut URL** : {transaction_checkout_url}
    # **Qr Code URL**: {transaction_qrcode_url}
    # **Transaction ID** : {transaction_id}

    # **Expire In :** {int(hours)}:{int(minutes)}:{int(seconds)}""",
    #                     buttons=addy_buttons,
    #                     link_preview=False,
    #                 )
    #                 add_eth_store(
    #                     query_user_id,
    #                     transaction_amount,
    #                     transaction_address,
    #                     transaction_timeout,
    #                     transaction_checkout_url,
    #                     transaction_qrcode_url,
    #                     transaction_id,
    #                     time.time(),
    #                 )
    #             else:
    #                 await event.client.send_message(
    #                     event.chat_id, f"Error : {transaction['error']}"
    #                 )
    #     elif addy == "bitcoin":
    #         btc_store = get_btc_store()
    #         addy_buttons = addy_button("bitcoin")
    #         if query_user_id in btc_store:
    #             (
    #                 transaction_amount,
    #                 transaction_address,
    #                 transaction_timeout,
    #                 transaction_checkout_url,
    #                 transaction_qrcode_url,
    #                 transaction_id,
    #                 main_time,
    #             ) = btc_store[query_user_id]
    #             time_since_last_message = time.time() - main_time
    #             if time_since_last_message > int(transaction_timeout):
    #                 remove_btc_store(query_user_id)
    #                 return await event.edit(
    #                     f"Link get expired exceed over time, click again to generate",
    #                     buttons=addy_buttons,
    #                 )
    #             remaining_time = int(transaction_timeout) - time_since_last_message
    #             hours = remaining_time // 3600
    #             remaining_seconds = remaining_time % 3600
    #             minutes = remaining_seconds // 60
    #             seconds = remaining_seconds % 60
    #             await event.edit(
    #                 f"""**💳 Bitcoin deposit**

    # To top up your balance, transfer the desired amount to this ETH address.

    # **Please note:**
    # 1. The deposit address is temporary and is only issued for 1 hour.
    # 2. One address accepts only one payment.

    # **BTC address** : `{transaction_address}`
    # **Transaction Amount**: {transaction_amount}
    # **CheckOut URL** : {transaction_checkout_url}
    # **Qr Code URL**: {transaction_qrcode_url}
    # **Transaction ID** : {transaction_id}

    # **Expire In :** {int(hours)}:{int(minutes)}:{int(seconds)}""",
    #                 buttons=addy_buttons,
    #                 link_preview=False,
    #             )
    #             return
    #         await event.delete()
    #         async with client.conversation(event.chat_id) as x:
    #             await x.send_message(
    #                 "**To top up your balance**,\n\nEnter the desired $ amount:"
    #             )
    #             old_amount = await x.get_response(timeout=1200)
    #             create_transaction_params = {
    #                 "amount": int(old_amount.text),
    #                 "currency1": "USD",
    #                 "currency2": "BTC",
    #             }
    #             transaction = crypto_client.createTransaction(create_transaction_params)
    #             if transaction["error"] == "ok":
    #                 transaction_amount = transaction["amount"]
    #                 transaction_address = transaction["address"]
    #                 transaction_timeout = transaction["timeout"] - 60
    #                 transaction_checkout_url = transaction["checkout_url"]
    #                 transaction_qrcode_url = transaction["qrcode_url"]
    #                 transaction_id = transaction["txn_id"]
    #                 hours = transaction_timeout // 3600
    #                 remaining_seconds = transaction_timeout % 3600
    #                 minutes = remaining_seconds // 60
    #                 seconds = remaining_seconds % 60
    #                 await event.client.send_message(
    #                     event.chat_id,
    #                     f"""**💳 Bitcoin deposit**

    # To top up your balance, transfer the desired amount to this LTC address.

    # **Please note:**
    # 1. The deposit address is temporary and is only issued for 1 hour.
    # 2. One address accepts only one payment.

    # **BTC address** : `{transaction_address}`
    # **Transaction Amount**: {transaction_amount}
    # **CheckOut URL** : {transaction_checkout_url}
    # **Qr Code URL**: {transaction_qrcode_url}
    # **Transaction ID** : {transaction_id}

    # **Expire In :** {int(hours)}:{int(minutes)}:{int(seconds)}""",
    #                     buttons=addy_buttons,
    #                     link_preview=False,
    #                 )
    #                 add_btc_store(
    #                     query_user_id,
    #                     transaction_amount,
    #                     transaction_address,
    #                     transaction_timeout,
    #                     transaction_checkout_url,
    #                     transaction_qrcode_url,
    #                     transaction_id,
    #                     time.time(),
    #                 )
    #             else:
    #                 await event.client.send_message(
    #                     event.chat_id, f"Error : {transaction['error']}"
    #                 )
    #     elif addy == "usdt":
    #         addy_buttons = addy_button("usdt")
    #         usdt_store = get_usdt_store()
    #         if query_user_id in usdt_store:
    #             (
    #                 transaction_amount,
    #                 transaction_address,
    #                 transaction_timeout,
    #                 transaction_checkout_url,
    #                 transaction_qrcode_url,
    #                 transaction_id,
    #                 main_time,
    #             ) = usdt_store[query_user_id]
    #             time_since_last_message = time.time() - main_time
    #             if time_since_last_message > int(transaction_timeout):
    #                 remove_usdt_store(query_user_id)
    #                 return await event.edit(
    #                     f"Link get expired exceed over time, click again to generate",
    #                     buttons=addy_buttons,
    #                 )
    #             remaining_time = int(transaction_timeout) - time_since_last_message
    #             hours = remaining_time // 3600
    #             remaining_seconds = remaining_time % 3600
    #             minutes = remaining_seconds // 60
    #             seconds = remaining_seconds % 60
    #             await event.edit(
    #                 f"""**💳 Tether USD deposit**

    # To top up your balance, transfer the desired amount to this ETH address.

    # **Please note:**
    # 1. The deposit address is temporary and is only issued for 1 hour.
    # 2. One address accepts only one payment.

    # **USDT trc-20 address** : `{transaction_address}`
    # **Transaction Amount**: {transaction_amount}
    # **CheckOut URL** : {transaction_checkout_url}
    # **Qr Code URL**: {transaction_qrcode_url}
    # **Transaction ID** : {transaction_id}

    # **Expire In :** {int(hours)}:{int(minutes)}:{int(seconds)}""",
    #                 buttons=addy_buttons,
    #                 link_preview=False,
    #             )
    #             return
    #         await event.delete()
    #         async with client.conversation(event.chat_id) as x:
    #             await x.send_message(
    #                 "**To top up your balance**,\n\nEnter the desired $ amount:"
    #             )
    #             old_amount = await x.get_response(timeout=1200)
    #             create_transaction_params = {
    #                 "amount": int(old_amount.text),
    #                 "currency1": "USD",
    #                 "currency2": "USDT.TRC20",
    #             }
    #             transaction = crypto_client.createTransaction(create_transaction_params)
    #             if transaction["error"] == "ok":
    #                 transaction_amount = transaction["amount"]
    #                 transaction_address = transaction["address"]
    #                 transaction_timeout = transaction["timeout"] - 60
    #                 transaction_checkout_url = transaction["checkout_url"]
    #                 transaction_qrcode_url = transaction["qrcode_url"]
    #                 transaction_id = transaction["txn_id"]
    #                 hours = transaction_timeout // 3600
    #                 remaining_seconds = transaction_timeout % 3600
    #                 minutes = remaining_seconds // 60
    #                 seconds = remaining_seconds % 60
    #                 await event.client.send_message(
    #                     event.chat_id,
    #                     f"""**💳 Tether USD deposit**

    # To top up your balance, transfer the desired amount to this LTC address.

    # **Please note:**
    # 1. The deposit address is temporary and is only issued for 1 hour.
    # 2. One address accepts only one payment.

    # **USDT trc-20 address** : `{transaction_address}`
    # **Transaction Amount**: {transaction_amount}
    # **CheckOut URL** : {transaction_checkout_url}
    # **Qr Code URL**: {transaction_qrcode_url}
    # **Transaction ID** : {transaction_id}

    # **Expire In :** {int(hours)}:{int(minutes)}:{int(seconds)}""",
    #                     buttons=addy_buttons,
    #                     link_preview=False,
    #                 )
    #                 add_usdt_store(
    #                     query_user_id,
    #                     transaction_amount,
    #                     transaction_address,
    #                     transaction_timeout,
    #                     transaction_checkout_url,
    #                     transaction_qrcode_url,
    #                     transaction_id,
    #                     time.time(),
    #                 )
    #             else:
    #                 await event.client.send_message(
    #                     event.chat_id, f"Error : {transaction['error']}"
    #                 )
    elif addy == "upi":
        addy_buttons = addy_button("upi")
        upi_store = get_upi_store()
        if query_user_id in upi_store:
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
                await event.reply(
                    f"Error checking UPI payment for user {query_user_id}: {e}"
                )
                return
            status = response_json["status"]
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
                link_preview=False,
            )
            return
        await event.delete()
        async with client.conversation(event.chat_id) as x:
            try:
                await x.send_message(
                    "**To top up your balance**,\nEnter the desired amount which you want to add:"
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
            link_preview=False,
        )
        add_upi_store(
            query_user_id, res_id, res_amount, res_name, res_email, res_short_url
        )


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
    upi_store = get_upi_store()
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
        players_balance = get_players_balance()
        if status == "paid":
            actual_amount = str(amount)[:-2]
            cut_2_percent = calculate_2_percent(actual_amount)
            after_cut_2_percent = float(actual_amount) - cut_2_percent
            old_balance = players_balance.get(user_id, 0)  # balance in ltc
            now_balance = after_cut_2_percent / 87  # balance in usdt
            balance_in_ltc = conversion("USDT", "LTC", now_balance)
            add_players_balance(user_id, float(old_balance) + float(balance_in_ltc))
            # Notify user about the balance update
            await client.send_message(
                user_id,
                f"Payment confirmed! Amount ${now_balance}\n\nYour Balance: ({players_balance[user_id]}) LTC",
            )
            remove_upi_store(user_id)


async def check_ltc_payments():
    ltc_store = get_ltc_store()
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
        players_balance = get_players_balance()
        if transactionInfo["error"] == "ok":
            status = transactionInfo["status_text"]
            if status == "Complete":
                net_fund = transactionInfo["netf"]  # received net balance inn ltc
                old_balance = players_balance.get(
                    user_id, 0
                )  # available balance in ltc
                now_balance = conversion("LTC", "USDT", net_fund)
                add_players_balance(user_id, float(old_balance) + float(net_fund))
                await client.send_message(
                    user_id,
                    f"Payment Confirmed! • LTC: {net_fund}, Added Balance : ${now_balance}, Balance: ({players_balance[user_id]} LTC)",
                )
                ltc_store.pop(user_id)


async def check_eth_payments():
    eth_store = get_eth_store()
    for user_id, payment_details in list(eth_store.items()):
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
            players_balance = get_players_balance()
            status = transactionInfo["status_text"]
            if status == "Complete":
                transactionInfo["receivedf"]
                net_fund = transactionInfo["netf"]
                params = {"cmd": "rates", "accepted": 1}
                rate = crypto_client.rates(params)
                from_rate = rate["USDT"]["rate_btc"]
                to_rate = rate["ETH"]["rate_btc"]
                conversion_rate = float(to_rate) / float(from_rate)
                old_balance = players_balance.get(user_id, 0)
                now_balance = str(conversion_rate * float(net_fund))[:10]
                add_players_balance(user_id, float(old_balance) + float(now_balance))
                await client.send_message(
                    user_id,
                    f"Payment Confirmed! • ETH: {net_fund}, Added Balance : ${now_balance}, Balance: {players_balance[user_id]}",
                )
                remove_eth_store(user_id)


async def check_btc_payments():
    btc_store = get_btc_store()
    for user_id, payment_details in list(btc_store.items()):
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
                players_balance = get_players_balance()
                transactionInfo["receivedf"]
                net_fund = transactionInfo["netf"]
                params = {"cmd": "rates", "accepted": 1}
                rate = crypto_client.rates(params)
                from_rate = rate["USDT"]["rate_btc"]
                to_rate = rate["BTC"]["rate_btc"]
                conversion_rate = float(to_rate) / float(from_rate)
                old_balance = players_balance.get(user_id, 0)
                now_balance = str(conversion_rate * float(net_fund))[:10]
                add_players_balance(user_id, float(old_balance) + float(now_balance))
                await client.send_message(
                    user_id,
                    f"Payment Confirmed! • BTC: {net_fund}, Added Balance : ${now_balance}, Balance: {players_balance[user_id]}",
                )
                remove_btc_store(user_id)


async def check_usdt_payments():
    usdt_store = get_usdt_store()
    for user_id, payment_details in list(usdt_store.items()):
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
            players_balance = get_players_balance()
            status = transactionInfo["status_text"]
            if status == "Complete":
                transactionInfo["receivedf"]
                net_fund = transactionInfo["netf"]
                params = {"cmd": "rates", "accepted": 1}
                rate = crypto_client.rates(params)
                from_rate = rate["USDT"]["rate_btc"]
                to_rate = rate["USDT"]["rate_btc"]
                conversion_rate = float(to_rate) / float(from_rate)
                old_balance = players_balance.get(user_id, 0)
                now_balance = str(conversion_rate * float(net_fund))[:10]
                add_players_balance(user_id, float(old_balance) + float(now_balance))
                await client.send_message(
                    user_id,
                    f"Payment Confirmed! • USDT: {net_fund}, Added Balance : ${now_balance}, Balance: {players_balance[user_id]}",
                )
                remove_usdt_store(user_id)


async def check_ltc_withdraw():
    with_ltc_store = get_with_ltc_store()
    for user_id, payment_details in list(with_ltc_store.items()):
        (
            transaction_amount,
            transaction_id,
        ) = payment_details
        post_params = {
            "cmd": "get_withdrawal_info",
            "id": transaction_id,
        }
        transaction_with_Info = crypto_client.getWithdrawalInfo(post_params)
        if transaction_with_Info["error"] == "ok":
            status = transaction_with_Info["status_text"]
            if status == "Cpmplete":
                net_fund = transaction_with_Info[
                    "amountf"
                ]  # net received balance in ltc
                players_balance = get_players_balance()
                old_balance = players_balance[user_id]  # available balance in ltc
                add_players_balance(user_id, float(old_balance) - float(net_fund))
                await client.send_message(
                    user_id,
                    f"Payment withdrawal Confirmed! • LTC: {net_fund}, Left Balance: **({players_balance[user_id]} LTC)**",
                )
                remove_with_ltc_store(user_id)


scheduler.add_job(check_upi_payments, "interval", minutes=5)
scheduler.add_job(check_ltc_payments, "interval", minutes=5)
scheduler.add_job(check_eth_payments, "interval", minutes=5)
scheduler.add_job(check_btc_payments, "interval", minutes=5)
scheduler.add_job(check_usdt_payments, "interval", minutes=5)
scheduler.add_job(check_ltc_withdraw, "interval", minutes=5)
scheduler.start()

# ==================== Start Client ==================#


client.start()
client.run_until_disconnected()
