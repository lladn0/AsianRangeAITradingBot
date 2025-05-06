import asyncio
from telegram import Bot as _TGBot
from io import BytesIO
from dotenv import load_dotenv
import os
from modules.base_bot import BaseBot

# Telegram bot class that sends screenshots or messages
class Bot(BaseBot):
    def __init__(self):
        load_dotenv()  # load API keys from .env file
        self._bot = _TGBot(token=os.getenv("TELEGRAM_TOKEN"))
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")

    def _run_async(self, coro):
        # this lets us call async methods from sync code
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            return asyncio.ensure_future(coro)
        else:
            return loop.run_until_complete(coro)

    def send_photo(self, data):
        # accepts either path or image bytes
        if isinstance(data, (bytes, bytearray)):
            bio = BytesIO(data)
            coro = self._bot.send_photo(self.chat_id, photo=bio)
        else:
            with open(data, "rb") as f:
                file_bytes = f.read()
                bio = BytesIO(file_bytes)
                coro = self._bot.send_photo(self.chat_id, photo=bio)
        self._run_async(coro)

    def send_message(self, text):
        # send text message
        coro = self._bot.send_message(self.chat_id, text)
        self._run_async(coro)
