import asyncio
import logging
import re

from telethon import Button, TelegramClient, events
from telethon.tl.types import InputMediaDice

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

round = {}

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
                Button.inline("ℹ️ Guide", data="diceguide"),
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
     
    
@client.on(events.CallbackQuery)
async def callback_query(event):
    query = event.data.decode("ascii").lower()
    query_user_id = event.query.user_id
    if query.startswith("cancel"):
        user_id = query.split("_")
        if query_user_id != int(user_id):
            return await event.answer(
                "Sorry, but you are not allowed to click others users button"
            )
    if query.startswith("normalmode"):
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
        text = query.split("_")
        user_id = text[1]
        round = text[2]
        if query_user_id != int(user_id):
            return await event.answer(
                "Sorry, but you are not allowed to click others users button"
            )
        if round == "5":
            points = 3
        elif round == "3":
            points = 2
        else:
            points = 1
        button = confirm_button(user_id, round)
        await event.edit(
        f"""🎲** Game Confirmation**

Your bet: $ amount
Win chance: 50/50
Win multiplier: 1.92x
Mode: First to {points} points
Game mode: Normal Mode""",
        buttons=button,
        )
    elif query.startswith("confirm"):
        text = query.split("_")
        user_id = text[1]
        round = text[2]
        if query_user_id != int(user_id):
            return await event.answer(
                "Sorry, but you are not allowed to click others users button"
            )
        await event.delete()
        user = await client.get_entity(int(user_id))
        if round == "5":
            points = 3
        elif round == "3":
            points = 2
        else:
            points = 1
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
            buttons=,
        )
    elif query.startswith("botwplayers"):
        text = query.split("_")
        user_id = text[1]
        round = text[2]
        if query_user_id != int(user_id):
            return await event.answer(
                "Sorry, but you are not allowed to click others users button"
            )
        await event.delete()
        my_bot = await client.get_me()
        user = await client.get_entity(user_id)
        game_mode[user.id] = ["botwplayers", int(round)]
        score[user_id] = [0, 0]
        await event.client.send_message(
            event.chat_id,
            f"""**🎲 Play with Bot**

Player 1: [{user.first_name}](tg://user?id={user.id})
Player 2: [{my_bot.first_name}](tg://user?id={my_bot.id})

**{user.first_name}** , your turn! To start, send a dice emoji: 🎲""",
        )
    elif query.startswith("playerwplayer"):
        await event.edit("Under Development")
        


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


@client.on(events.NewMessage(incoming=True))
async def gameplay(event):
    if not event.sender_id in game_mode:
        return
    if event.text:
        return
    gamemode, times = game_mode[event.sender_id]
    my_bot = await client.get_me()
    user = await client.get_entity(event.sender_id)
    score_player1, score_player2 = score[event.sender_id]
    current_round = round.get(event.sender_id, 1)
    if gamemode == "botwplayers":
        player1 = event.media.value
        await asyncio.sleep(4)
        await event.reply("Now it's my turn")
        bot_player = await event.reply(file=InputMediaDice(emoticon="🎲"))
        await asyncio.sleep(4)
        player2 = bot_player.media.value
        if player1 > player2:
            score_player1 += 1
            score[event.sender_id] = [score_player1, score_player2]
        elif player1 < player2:
            score_player2 += 1
            score[event.sender_id] = [score_player1, score_player2]
        else:
            current_round -= 1
        if times == current_round:
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
            game_mode.pop(event.sender_id)
            round.pop(event.sender_id)
            return
        await event.respond(
            f"""**Score**

{user.first_name}: {score_player1}
{my_bot.first_name}: {score_player2}

**{user.first_name}**, it's your turn!""",
        )
        round[event.sender_id] = current_round + 1



# ==================== Start Client ==================#

client.run_until_disconnected()

# if len(sys.argv) in {1, 3, 4}:
#     with contextlib.suppress(ConnectionError):
#         client.run_until_disconnected()
# else:
#     client.disconnect()
