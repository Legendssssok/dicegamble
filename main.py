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
            Button.inline("5 Round", data="round_{user_id}_5"),
        ],
        [
            Button.inline("3 Round", data="round_{user_id}_3"),
        ],
        [
            Button.inline("1 Round", data="round_{user_id}_1"),
        ],
    ]
    return points_button


@client.on(events.CallbackQuery)
async def callback_query(event):
    query = event.data.decode("ascii").lower()
    query_user_id = event.query.user_id
    if query.startswith("cancel"):
        user_id = query.split("_")
        if query_user_id != int(user_id):
            return await event.answer("Sorry, but you are not allowed to click others users button")
    if query.startswith("normalmode"):
        user_id = query.split("_")[1]
        if query_user_id != int(user_id):
            return await event.answer("Sorry, but you are not allowed to click others users button")
        await event.edit(
            "🎲 Choose the number of rouns to win",
            buttons=points_button,
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




# ======= Five all handle ========#

five_confirm_button = [
    [
        Button.inline("✅ Confirm", data="fve_confirm_button"),
        Button.inline("❌ Cancel", data="cancel"),
    ]
]


@client.on(events.callbackquery.CallbackQuery(data=re.compile(b"5_round")))
async def fierus(event):
    await event.edit(
        """🎲** Game Confirmation**

Your bet: $1.00
Win chance: 50/50
Win multiplier: 1.92x
Mode: First to 3 points
Game mode: Normal Mode""",
        buttons=five_confirm_button,
    )


final5_confirm_button = [
    [
        Button.inline("✅ Accept Match", data="playerwplayer"),
        Button.inline("✅ Play against bot", data="5botwplayer"),
    ],
    [
        Button.inline("❌ Cancel", data="cancel"),
    ],
]


@client.on(events.callbackquery.CallbackQuery(data=re.compile(b"fve_confirm_button")))
async def fi5erus(event):
    await event.delete()
    await client.get_me()
    user = await client.get_entity(event.sender_id)
    await event.client.send_message(
        event.chat_id,
        f"""{user.first_name} wants to play dice!

Bet: $1.00
Win chance: 50/50
Win multiplier: 1.92x
Mode: First to 3 points

Normal Mode
Basic game mode. You take turns rolling the dice, and whoever has the highest digit wins the round.

If you want to play, click the "Accept Match" button""",
        buttons=final5_confirm_button,
    )


@client.on(events.callbackquery.CallbackQuery(data=re.compile(b"5botwplayer")))
async def fie5rndus(event):
    await event.delete()
    times = 5
    my_bot = await client.get_me()
    user = await client.get_entity(event.sender_id)
    game_mode[user.id] = ["botwplayers", times]
    score[event.sender_id] = [0, 0]
    await event.client.send_message(
        event.chat_id,
        f"""**🎲 Play with Bot**

Player 1: [{user.first_name}](tg://user?id={user.id})
Player 2: [{my_bot.first_name}](tg://user?id={my_bot.id})

**{user.first_name}** , your turn! To start, send a dice emoji: 🎲""",
    )


# ======== 3 All Handle ========


three_confirm_button = [
    [
        Button.inline("✅ Confirm", data="thee_confirm_button"),
        Button.inline("❌ Cancel", data="cancel"),
    ]
]


@client.on(events.callbackquery.CallbackQuery(data=re.compile(b"3_round")))
async def fierus(event):
    await event.edit(
        """🎲** Game Confirmation**

Your bet: $1.00
Win chance: 50/50
Win multiplier: 1.92x
Mode: First to 2 points
Game mode: Normal Mode""",
        buttons=three_confirm_button,
    )


final3_confirm_button = [
    [
        Button.inline("✅ Accept Match", data="playerwplayer"),
        Button.inline("✅ Play against bot", data="3botwplayer"),
    ],
    [
        Button.inline("❌ Cancel", data="cancel"),
    ],
]


@client.on(events.callbackquery.CallbackQuery(data=re.compile(b"thee_confirm_button")))
async def fierus(event):
    await event.delete()
    await client.get_me()
    user = await client.get_entity(event.sender_id)
    await event.client.send_message(
        event.chat_id,
        f"""{user.first_name} wants to play dice!

Bet: $1.00
Win chance: 50/50
Win multiplier: 1.92x
Mode: First to 3 points

Normal Mode
Basic game mode. You take turns rolling the dice, and whoever has the highest digit wins the round.

If you want to play, click the "Accept Match" button""",
        buttons=final3_confirm_button,
    )


@client.on(events.callbackquery.CallbackQuery(data=re.compile(b"3botwplayer")))
async def fien3dus(event):
    await event.delete()
    times = 3
    my_bot = await client.get_me()
    user = await client.get_entity(event.sender_id)
    game_mode[user.id] = ["botwplayers", times]
    score[event.sender_id] = [0, 0]
    await event.client.send_message(
        event.chat_id,
        f"""**🎲 Play with Bot**

Player 1: [{user.first_name}](tg://user?id={user.id})
Player 2: [{my_bot.first_name}](tg://user?id={my_bot.id})

**{user.first_name}** , your turn! To start, send a dice emoji: 🎲""",
    )


# ============ 1 All Handle ===========


# ==================== Start Client ==================#

client.run_until_disconnected()

# if len(sys.argv) in {1, 3, 4}:
#     with contextlib.suppress(ConnectionError):
#         client.run_until_disconnected()
# else:
#     client.disconnect()
