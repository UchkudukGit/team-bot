#!/usr/bin/env python

import logging
import re
from typing import Any

import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

import config
from db import event_repo
from models import ButtonAction, Event, EventStatus, ShortUser

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
                [
                    InlineKeyboardButton("🏁 Закрыть сбор",
                                         callback_data=ButtonAction.CLOSE_EVENT.value),
                ],
                [
                    InlineKeyboardButton("✅ Я иду",
                                         callback_data=ButtonAction.ADD_ACTIVE_USER.value),
                    InlineKeyboardButton("❌ Я не иду",
                                         callback_data=ButtonAction.ADD_INACTIVE_USER.value),
                ],
                [
                    InlineKeyboardButton("плюс 1️⃣",
                                         callback_data=ButtonAction.ADD_FROM_ME.value),
                    InlineKeyboardButton("минус 1️⃣",
                                         callback_data=ButtonAction.REMOVE_FROM_ME.value),
                ],
            ]
        case EventStatus.CLOSED:
            return [
                [
                    InlineKeyboardButton("↩️ Открыть сбор",
                                         callback_data=ButtonAction.OPEN_EVENT.value),
                    InlineKeyboardButton("❌ Удалить сбор",
                                         callback_data=ButtonAction.DELETE_EVENT.value),
                ]
            ]
        case EventStatus.DELETED:
            return [
                [
                    InlineKeyboardButton("↩️ Открыть сбор",
                                         callback_data=ButtonAction.OPEN_EVENT.value),
                    InlineKeyboardButton("❌ Удалить безвозвратно",
                                         callback_data=ButtonAction.DELETE_COMPLETELY.value),
                ]
            ]


def get_markup(event: Event) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(def_keyboard(event.status))

def parse_args(s) -> dict[str, str]:
    # Регулярное выражение для поиска пар ключ=значение
    pattern = r'(\w+)=(".*?"|\S+)'
    matches = re.findall(pattern, s)

    # Преобразуем список кортежей в словарь
    result = {key: value.strip('"') for key, value in matches}
    return result

def get_event_args(update: Update, context: ContextTypes.DEFAULT_TYPE) -> dict[str, str]:
    user = update.message.from_user
    args = ' '.join(context.args)
    event_args={'owner':ShortUser.from_user(user), 'name': 'event'}
    if not args:
        return event_args

    dict_args = parse_args(args)
    if not dict_args:
        event_args['name'] = args
        return event_args
    event_args.update(dict_args)
    return event_args


def create_event(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Event:
    return Event(**get_event_args(update, context))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await help_command(update, context)

async def event(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    event = create_event(update, context)

    message = await context.bot.send_message(
        chat_id=update.message.chat_id,
        text=event.to_str(),
        reply_markup=get_markup(event))
    event.create_key(message.chat_id, message.message_id)
    event_repo.save_event(event)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    event = event_repo.get_event(*get_key(query.message))

    user = query.from_user
    match query.data:
        case ButtonAction.ADD_ACTIVE_USER.value:
            if not event.add_active_user(user):
                return
        case ButtonAction.ADD_INACTIVE_USER.value:
            if not event.add_inactive_user(user):
                return
        case ButtonAction.ADD_FROM_ME.value:
            event.add_user_from_me(user)
        case ButtonAction.REMOVE_FROM_ME.value:
            if not event.remove_user_from_me(user):
                return
        case ButtonAction.OPEN_EVENT.value:
            event.status = EventStatus.OPENED
        case ButtonAction.CLOSE_EVENT.value:
            event.status = EventStatus.CLOSED
        case ButtonAction.DELETE_EVENT.value:
            if event.is_owner(user):
                event.status = EventStatus.DELETED
        case ButtonAction.DELETE_COMPLETELY.value:
            if event.is_owner(user):
                await query.message.delete()
                event_repo.delete_event(event)
                return

    event_repo.save_event(event)
    try:
        await query.message.edit_text(
            text=event.to_str(),
            reply_markup=get_markup(event))
    except telegram.error.BadRequest as e:
        logger.info(e.message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = '''Бот для сбора участников для события
Что бы открыть сбор необходимо использовать команду /event
Варианты начала события:
/event - создаст событие с неограниченным кол-ом участников
/event Играем в футбол в четверг в 20:00 - создаст событие c именем
/event name="пьянка" limit=12 - создаст событие c именем и ограничением по кол-ву участников
/event name="пьянка" limit=12 reserve=2  - создаст событие c именем и ограничением по кол-ву участников и запасных

    '''
    await update.message.reply_text(text)


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
