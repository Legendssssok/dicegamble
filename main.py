import asyncio
import base64
import contextlib
import ipaddress
import logging
import os
import random
import re
import struct
import sys
from datetime import datetime

import psutil
from pyrogram import Client
from pyrogram import errors as pyro_errors
from pyrogram.storage.storage import Storage
from telethon import Button, TelegramClient, errors, events
from telethon.sessions import StringSession
from telethon.sessions.string import _STRUCT_PREFORMAT, CURRENT_VERSION, StringSession
from telethon.tl.functions.channels import JoinChannelRequest

API_ID = 
API_HASH = 
TOKEN = 

logging.basicConfig(
    format="[%(asctime)s] [%(levelname)s] [%(name)s] : %(message)s",
    level=logging.ERROR,
    datefmt="%H:%M:%S",
)

LOGS = logging.getLogger("Dice bot")

client = TelegramClient("LegendBoy", API_ID, API_HASH).start(bot_token=TOKEN)


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

# ==================== Start Client ==================#
if len(sys.argv) in {1, 3, 4}:
    with contextlib.suppress(ConnectionError):
        client.run_until_disconnected()
else:
    client.disconnect()
