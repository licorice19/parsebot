from dotenv import load_dotenv
import asyncio
import os
import telegram
from telegram import Update
from telegram.ext import filters, ApplicationBuilder, CommandHandler, ContextTypes
from typing import Union, List
import logging

load_dotenv()

TOKEN = os.environ.get("TOKEN")
PASSWORD = os.environ.get("PASSWORD")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def create_profile(user_id):
    pass


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Введите пароль!")
    logging.debug(msg=f"{update.effective_chat.id}")


def bot_init():
    application = ApplicationBuilder().token(TOKEN).build()

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    application.run_polling()