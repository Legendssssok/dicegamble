import asyncio
import logging
import re
import time

from telethon import Button, TelegramClient, events, functions, types
from telethon.tl.types import BotCommand, InputMediaDice

API_ID = 11573285
API_HASH = "f2cc3fdc32197c8fbaae9d0bf69d2033"
TOKEN = "7213709392:AAGXvbg9v_CqtWCrg270pBHT2-qXe2DWWNw"

logging.basicConfig(
    format="[%(asctime)s] [%(levelname)s] [%(name)s] : %(message)s",
    level=logging.ERROR,
    datefmt="%H:%M:%S",
)

LOGS = logging.getLogger("Dice bot")

client = TelegramClient("LegendBoy", API_ID, API_HASH).start(bot_token=TOKEN)


game_mode = {}

score = {}

count_round = {}

player_turn = {}

old_score = {}

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
        await event.client.send_message(
            event.chat_id,
            """🏠 Menu

Your balance: $0.00 (0.00000 LTC)""",
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
    if event.sender_id in game_mode:
        return await event.reply("Your previous game is yet not finished")
    text = event.text.split(" ")
    try:
        int(text[1])
    except:
        return await event.reply(
            """🎲 Play Dice

To play, type the command /dice with the desired bet.

Examples:
/dice 5.50 - to play for $5.50"""
        )
    await event.client.send_message(
        event.chat_id,
        f"🎲 Choose the game mode",
        buttons=[
            [
                Button.inline("Normal Mode", data=f"normalmode_{event.sender_id}"),
            ],
            [
                Button.inline("Double Roll", data="doubleroll"),
            ],
            [
                Button.inline("Crazy Mode", data="crazymode"),
            ],
            [
                Button.inline("ℹ️ Guide", data=f"diceguide_{event.sender_id}"),
                Button.inline("❌ Cancel", data=f"cancel_{event.sender_id}"),
            ],
        ],
    )


def point_button(user_id):
    points_button = [
        [
            Button.inline("5 Round", data=f"round_{user_id}_5"),
        ],
        [
            Button.inline("3 Round", data=f"round_{user_id}_3"),
        ],
        [
            Button.inline("1 Round", data=f"round_{user_id}_1"),
        ],
    ]
    return points_button


def confirm_button(user_id, round):
    confirms_button = [
        [
            Button.inline("✅ Confirm", data=f"confirm_{user_id}_{round}"),
            Button.inline("❌ Cancel", data=f"cancel_{user_id}"),
        ]
    ]
    return confirms_button


def final_confirm_button(user_id, round):
    final_confirms_button = [
        [
            Button.inline("✅ Accept Match", data=f"playerwplayer_{user_id}_{round}"),
            Button.inline("✅ Play against bot", data=f"botwplayer_{user_id}_{round}"),
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
        user_id = query.split("_")[1]
        if query_user_id != int(user_id):
            return await event.answer(
                "Sorry, but you are not allowed to click others users button"
            )
        button = point_button(user_id)
        await event.edit(
            "🎲 Choose the number of rouns to win",
            buttons=button,
        )
    elif query.startswith("round"):
        user_id, round = query.split("_")[1:3]
        if query_user_id != int(user_id):
            return await event.answer(
                "Sorry, but you are not allowed to click others users button"
            )
        points = {"5": 3, "3": 2, "1": 1}[round]
        await event.edit(
            f"""🎲** Game Confirmation**

Your bet: $ amount
Win chance: 50/50
Win multiplier: 1.92x
Mode: First to {points} points
Game mode: Normal Mode""",
            buttons=confirm_button(user_id, round),
        )
    elif query.startswith("confirm"):
        user_id, round = query.split("_")[1:3]
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

Bet: Soon
Win chance: 50/50
Win multiplier: 1.92x
Mode: First to {points} points

Normal Mode
Basic game mode. You take turns rolling the dice, and whoever has the highest digit wins the round.

If you want to play, click the "Accept Match" button""",
            buttons=final_confirm_button(user_id, round),
        )
    elif query.startswith("botwplayer"):
        user_id, round = query.split("_")[1:3]
        if query_user_id != int(user_id):
            return await event.answer(
                "Sorry, but you are not allowed to click others users button"
            )
        await event.delete()
        my_bot = await client.get_me()
        user = await client.get_entity(int(user_id))
        game_mode[user.id] = ["botwplayers", int(round)]
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
        user_id, round = query.split("_")[1:3]
        if query_user_id == int(user_id):
            return await event.answer("You cannot accept your own match")
        await event.delete()
        player1 = await client.get_entity(int(user_id))
        player2 = await client.get_entity(query_user_id)
        score[player1.id] = [0, 0]
        game_mode[int(user_id)] = ["playerwplayer", int(round), query_user_id]
        game_mode[query_user_id] = ["playerwplayer", int(round), int(user_id)]
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
    user_id = query.split("_")[1]
    query_user_id = event.query.user_id
    if query_user_id != int(user_id):
        return await event.answer(
            "Sorry, but you are not allowed to click others users button"
        )
    await event.edit(
        f"🎲 Choose the game mode",
        buttons=[
            [
                Button.inline("Normal Mode", data=f"normalmode_{user_id}"),
            ],
            [
                Button.inline("Double Roll", data="doubleroll"),
            ],
            [
                Button.inline("Crazy Mode", data="crazymode"),
            ],
            [
                Button.inline("ℹ️ Guide", data=f"diceguide_{user_id}"),
                Button.inline("❌ Cancel", data=f"cancel_{event.sender_id}"),
            ],
        ],
    )


def back_groups(user_id):
    back_group = [[Button.inline("⬅️ Back", data=f"back_{user_id}")]]
    return back_group


@client.on(events.callbackquery.CallbackQuery(data=re.compile(b"diceguide_")))
async def diceguide(event):
    query = event.data.decode("ascii").lower()
    user_id = query.split("_")[1]
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
        buttons=back_groups(user_id),
    )


@client.on(events.callbackquery.CallbackQuery(data=re.compile(b"home")))
async def home(event):
    if event.is_private:
        await event.edit(
            """🏠 Menu

Your balance: $0.00 (0.00000 LTC)""",
            buttons=game,
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
    if not event.sender_id in game_mode:
        return
    if not event.media.emoticon == "🎲":
        return
    if event.sender_id in last_message_times:
        max_time = 9
        time_since_last_message = time.time() - last_message_times[event.sender_id]
        if time_since_last_message < int(max_time):
            return
    my_bot = await client.get_me()
    user = await client.get_entity(event.sender_id)
    gamemode, round = game_mode[event.sender_id][:2]
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
            game_mode.pop(event.sender_id)
            count_round.pop(event.sender_id)
            if score_player1 > score_player2:
                winner = f"🎉 Congratulations! {user.first_name} You won"
            elif score_player1 < score_player2:
                winner = f"🎉 Congratulations! {my_bot.first_name} I Won"
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

**{user.first_name}**, it's your turn!""",
        )
        count_round[event.sender_id] = current_round + 1
    elif gamemode == "playerwplayer":
        if player_turn[event.sender_id] != event.sender_id:
            return await event.reply("It's not your turn")
        last_message_times[event.sender_id] = time.time()
        player1 = event.media.value
        player1_details = await client.get_entity(event.sender_id)
        opponent_id = game_mode[event.sender_id][2]
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
                game_mode.pop(event.sender_id)
                count_round.pop(player2.id)
                old_score.pop(event.sender_id)
                if score_player1 > score_player2:
                    winner = f"🎉 Congratulations! {player2.first_name}  you won"
                elif score_player1 < score_player2:
                    winner = f"🎉 Congratulations! {player1_details.first_name} You Won"
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

**{player2.first_name}**, it's your turn!"""
            )
            count_round[player2.id] = current_round + 1
        else:
            current_round = count_round[event.sender_id]
            old_score[player2.id] = [player1]
            await event.reply(f"{player2.first_name} your turn")
            count_round[event.sender_id] = current_round + 1

# ============ balance, deposit, withdrawal =========#



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
                scope=types.BotCommandScopeDefault(), lang_code="en", commands=commands))
        await event.client.send_message(event.chat_id, f"{result}")
    except Exception as e:
        await event.reply(f"Error : {e}")


# ==================== Start Client ==================#

client.run_until_disconnected()
