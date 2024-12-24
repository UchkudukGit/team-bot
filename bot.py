import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

import config

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(context.user_data.values())
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f'hello, {user.first_name or user.username}')


if __name__ == '__main__':
    application = ApplicationBuilder().token(config.token).build()

    start_handler = CommandHandler('start', start)
    hello_handler = CommandHandler('hello', hello)
    application.add_handler(start_handler)
    application.add_handler(hello_handler)

    application.run_polling()