import asyncio
import contextlib
import logging
import re
import sys

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
    if event.media.emoticon != "🎲":
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
                winner = user.first_name
            elif score_player1 < score_player2:
                winner = my_bot.first_name
            await event.client.send_message(
                event.chat_id,
                f"""🏆 **Game over!**

**Score:**
{user.first_name} • {score_player1}
{my_bot.first_name} • {score_player2}

🎉 Congratulations! {winner} You won""",
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
    times = int(text[1])
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


# ==================== Start Client ==================#
if len(sys.argv) in {1, 3, 4}:
    with contextlib.suppress(ConnectionError):
        client.run_until_disconnected()
else:
    client.disconnect()
