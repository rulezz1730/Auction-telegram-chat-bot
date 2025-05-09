from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_ID


def admin_only(func):
    """Декоратор: доступ только для админов"""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Проверяем, что пользователь вызвавший команду — это админ
        if update.effective_user.id not in ADMIN_ID:
            if update.message:
                await update.message.reply_text("🚫 Даже не пытайся дать мне команду, ты не админ")
            elif update.callback_query:
                await update.callback_query.answer("🚫 Даже не пытайся нажимать кнопку, ты не админ", show_alert=True)
            return
        return await func(update, context)
    return wrapper