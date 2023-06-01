#!/usr/bin/env python
# pylint: disable=unused-argument, wrong-import-position
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to reply to Telegram messages.

First, a few handler functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""
import json
import logging
import os
import sys

import hupper
from messages_db import clear_messages, get_messages, put_message_list
from prompts import MAIN_PROMPT
from telegram import Bot, ForceReply, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from clova_util import clova_create

BOT_TOKEN = os.environ["BOT_TOKEN"]

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
        reply_markup=ForceReply(selective=True),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Help!")


async def newchat_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /newchat is issued."""
    clear_messages(user_id=update.message.from_user.id)
    logger.info(f"New chat for user {update.message.from_user.id}")
    await update.message.reply_text("Let's do New Chat!")


async def clovaup_stream(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = await update.message.reply_text("...")

    user = update.message.from_user
    user_id = user.id
    first_name = user.first_name

    system_message = {"role": "system", "content": MAIN_PROMPT}
    new_message = {"role": "user", "content": f"{first_name}: {update.message.text}"}
    messages = [system_message] + get_messages(user_id=user_id) + [new_message]

    # Show messages in logs using lazy % formatting
    logger.info("Messages: %s", json.dumps(messages, indent=2))

    response = await clova_create_callback_tba(
        messages=messages,
        call_back_func=context.bot.edit_message_text,
        call_back_args={
            "chat_id": update.message.chat_id,
            "message_id": msg.message_id,
        },
    )

    await context.bot.edit_message_text(
        chat_id=update.message.chat_id,
        message_id=msg.message_id,
        text=response,
        parse_mode=ParseMode.MARKDOWN,
    )

    # Update DB
    put_message_list(
        user_id=user_id,
        message_list=[new_message, {"role": "assistant", "content": response}],
    )


async def clova_up(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = await update.message.reply_text("...")

    user = update.message.from_user
    user_id = user.id

    new_message = {"role": "user", "content": f"{update.message.text}"}
    messages = get_messages(user_id=user_id) + [new_message]

    response = clova_create(messages=messages)
    if "content" not in response:
        response_text = "Sorry, there is an error." + str(response)
        logger.error(response_text)
    else:
        response_text = response["content"]

    await context.bot.edit_message_text(
        chat_id=update.message.chat_id,
        message_id=msg.message_id,
        text=response_text,
        parse_mode=ParseMode.MARKDOWN,
    )

    # Update DB
    put_message_list(
        user_id=user_id,
        message_list=[new_message, {"role": "assistant", "content": response_text}],
    )


def main_hanlder(event=None, context=None) -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(BOT_TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("newchat", newchat_command))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, clova_up))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


def start_reloader():
    """Start the reloader"""
    reloader = hupper.start_reloader("clova_up.main_hanlder", verbose=True)
    sys.exit(reloader.wait_for_exit())


if __name__ == "__main__":
    if "reload" in sys.argv:
        start_reloader()
    else:
        # Run the async main function
        main_hanlder()
