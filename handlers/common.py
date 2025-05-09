from telegram import Update
from telegram.ext import ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('🤖 Всем здравия! Я бот для аукционов!')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📘 Доступные команды:\n"
        "/start — приветствие\n"
        "/new_auc Название лота (1 слово или слитно), Дата в формате 'ГГГГ-ММ-ДД', время начала 'ЧЧ:ММ', время конца 'ЧЧ:ММ', Стартовая цена - ЧИСЛО, Шаг ставки - ЧИСЛО\n"
        "/show_aucs — показать активные\n"
        # "/cancel_auc — отменить последний\n"
        "/delete_auc <номер> — 🗑 удалить по номеру\n",
    )