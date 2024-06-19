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

from config import *

api_id = API_ID
api_hash = API_HASH

logging.basicConfig(
    format="[%(asctime)s] [%(levelname)s] [%(name)s] : %(message)s",
    level=logging.ERROR,
    datefmt="%H:%M:%S",
)

LOGS = logging.getLogger("ForwardBot")

client = TelegramClient("LegendBoy", API_ID, API_HASH).start(bot_token=TOKEN)


@client.on(events.NewMessage(pattern="/start"))
async def start(event):
    await event.reply(
        "**Greetings!**\n\nPlay dice with yo",
    )



async def startup_process():
  try:
    await client.send_message(
      i,
      f"#START\n\n**Version** :- α • 1.0\n**Developed By** : Legend [ Developer / Bot Maker ]\n\nYour Dice Gamble Bot Has Been Started Successfully",
    )
  except:
    pass


client.loop.run_until_complete(startup_process())


# ==================== Start Client ==================#
if len(sys.argv) in {1, 3, 4}:
    with contextlib.suppress(ConnectionError):
        client.run_until_disconnected()
else:
    client.disconnect()
