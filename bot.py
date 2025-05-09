import logging
from datetime import time
from zoneinfo import ZoneInfo

from telegram.ext import (
    ApplicationBuilder, #Создание и настройка бота
    CommandHandler, #Обработчик команд типа /start /new_auction
    CallbackQueryHandler,
    MessageHandler,
    filters,
    Application
    )

from config import TOKEN
from handlers.common import start, help_command
from handlers.admin_commands import new_auc, show_aucs, delete_auc
from handlers.callbacks import handle_callback
from services.bid_service import process_user_bid_message
from services.auction_lifecycle import restore_scheduled_tasks
from services.backup import make_backup
from data.database import init_db


# Инициализация БД
init_db()

#Настройка логгирования в консоль
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', # Шаблон лог-сообщения
    level = logging.INFO # Уровень логов: INFO — стандартный, показывает всё важно
    )

# Восстановление отложенных задач при старте
async def post_init(app: Application):
    await restore_scheduled_tasks(app)

# Точка входа
def main():
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build() # Создаём "приложение" бота, передаём ему токен

    # Ежедневное резервное копирование БД
    app.job_queue.run_daily(
        callback=lambda ctx: make_backup(),
        time=time(hour=13, minute=00, tzinfo=ZoneInfo("Europe/Moscow"))
    )

     # Регистрация обработчиков команд
    app.add_handler(CommandHandler("start", start)) #Запуск бота, приветствие
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("new_auc", new_auc)) #Создание аукциона
    app.add_handler(CommandHandler("show_aucs", show_aucs)) #Проверяем аукционы
    app.add_handler(CommandHandler('delete_auc', delete_auc)) #Удаляем аукцион по его номеру

    # Обработка ставок
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_user_bid_message))

    # Обработка Кнопок (inline)
    app.add_handler(CallbackQueryHandler(handle_callback)) #Коллбэк для вызову функции по удалению аукциона по номеру

    print("🤖 Бот аукциона запущен!")
    app.run_polling()
    
if __name__ == "__main__":
    main()


   