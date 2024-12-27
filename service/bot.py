#!/usr/bin/env python

import logging
from typing import Any

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, User, Message
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

import config
from db import event_repo
from service.models import ButtonAction, Event, EventStatus

event_repo = event_repo.EventRepo()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def get_key(message: Any) -> tuple[int, int]:
    return message.chat_id, message.message_id


def def_keyboard(event_status: EventStatus) -> list[list[InlineKeyboardButton]]:
    match event_status:
        case EventStatus.OPENED:
            return [
                [InlineKeyboardButton("Закрыть сбор",
                                      callback_data=ButtonAction.CLOSE_EVENT.value), ],
                [
                    InlineKeyboardButton("Я иду",
                                         callback_data=ButtonAction.ADD_ACTIVE_USER.value),
                    InlineKeyboardButton("Я не иду",
                                         callback_data=ButtonAction.ADD_INACTIVE_USER.value),
                ],
            ]
        case EventStatus.CLOSED:
            return [[InlineKeyboardButton("Открыть сбор",
                                         callback_data=ButtonAction.OPEN_EVENT.value), ]]


def get_markup(event: Event) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(def_keyboard(event.status))


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await event(update, context)


async def event(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    event = Event(event_name='event')
    message = await update.message.reply_text(event.to_str(), reply_markup=get_markup(event))
    event.create_key(message.chat_id, message.message_id)
    event_repo.save_event(event)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    key = get_key(query.message)
    await query.answer()

    event = event_repo.get_event(*key)

    user = query.from_user
    match query.data:
        case ButtonAction.ADD_ACTIVE_USER.value:
            event.add_active_user(user)
        case ButtonAction.ADD_INACTIVE_USER.value:
            event.add_inactive_user(user)
        case ButtonAction.OPEN_EVENT.value:
            event.status = EventStatus.OPENED
        case ButtonAction.CLOSE_EVENT.value:
            event.status = EventStatus.CLOSED

    event_repo.save_event(event)
    await query.message.edit_text(text=event.to_str(), reply_markup=get_markup(event))


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Use /event <event_name> for start event")


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(config.token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))

    application.add_handler(CommandHandler("event", event))
    application.add_handler(CallbackQueryHandler(button))

    application.add_handler(CommandHandler("help", help_command))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
