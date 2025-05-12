import asyncio
import uuid
from utils.decorators import admin_only
from datetime import datetime
from zoneinfo import ZoneInfo
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from data.database import insert_auction, delete_auction
from data.models import Auction
from data.storage import auction_data, archived_auctions, scheduled_tasks
from utils.helpers import title_parser_new_auc, check_overlap
from services.auction_lifecycle import schedule_auction_start, schedule_auction_end

# Обработчик команды /new_auc, доступен только админу
@admin_only
async def new_auc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Создание нового аукциона"""
    chat_id = update.effective_chat.id
    try:
        if len(context.args) < 6:
            await update.message.reply_text(
                 "⚠️ Неверное количество параметров.\n\n"
                 "Используй:\n\n"
                 "/new_auc Название лота, Дата в формате 'ГГГГ-ММ-ДД', время начала 'ЧЧ:ММ', время конца 'ЧЧ:ММ', Стартовая цена - ЧИСЛО, Шаг ставки - ЧИСЛО",
                )
            return
        
        # Парсер для нескольких слов в названии
        parsed = title_parser_new_auc(context.args)
        if not parsed:
        # if parsed is None:
            await update.message.reply_text(
                "⚠️ Неверное количество параметров.\n\n"
                "Формат: /new_auc Название лота (несколько слов) Дата Время начала Время конца Старт Шаг",
            )
            return

        title, date_str, start_time_str, end_time_str, start_bid_str, step_str = parsed

        # Преобразуем дату и время в datetime
        try:
            moscow_tz = ZoneInfo("Europe/Moscow")
            start_dt = datetime.strptime(f"{date_str} {start_time_str}", "%Y-%m-%d %H:%M").replace(tzinfo=moscow_tz)
            end_dt = datetime.strptime(f"{date_str} {end_time_str}", "%Y-%m-%d %H:%M").replace(tzinfo=moscow_tz)
        except:
            await update.message.reply_text("❌ Неверный формат даты или времени. Пример: 2025-04-21 18:00 18:10")
            return
        
       #Преобразование вводных в числа - начальная ставка и шаг
        try:
            start_bid = int(start_bid_str)
            step = int(step_str)
        except:
            await update.message.reply_text("❌ Стартовая цена и шаг ставки должны быть целыми числами.")
            return

        #Проверка - окончание аука должно быть позже начала
        if end_dt <= start_dt:
            await update.message.reply_text("⛔ Время окончания должно быть позже времени начала.")
            return
        
        # Проверка начала аукциона - начало аукциона не должно быть раньше текущего времени
        now = datetime.now(ZoneInfo("Europe/Moscow"))
        if start_dt <= now:
            await update.message.reply_text(
                "⛔ Нельзя создать аукцион на прошедшее или текущее время. Выбери более позднее время."
            )
            return
        
        # Проверка пересечений
        overlap_found, conflicting_auc = check_overlap(chat_id, start_dt, end_dt)
        if overlap_found:
            await update.message.reply_text(
                f"❌ Нельзя создать аукцион!\n\n"
                f"⏰ Пересечение с другим аукционом: «{conflicting_auc.title}»\n"
                f"🗓️ {conflicting_auc.start_dt.strftime('%d.%m.%Y %H:%M')} - {conflicting_auc.end_dt.strftime('%H:%M')}",
            )
            return

        auction = Auction(
            id=str(uuid.uuid4()),
            chat_id=chat_id,
            title=title,
            start_dt=start_dt,
            end_dt=end_dt,
            start_bid=start_bid,
            step=step,
            is_active=True,
            is_running=False,
            is_finish=False,
            last_valid_bid=start_bid,
            invalid_count=0,
            can_count_invalid=True,
            is_paused=False,
            all_bids=[],
            all_bets_placed=[]
        )
        if chat_id not in auction_data:
            auction_data[chat_id]=[]

        auction_data[chat_id].append(auction)
        insert_auction(auction)
        
        start_task = asyncio.create_task(schedule_auction_start(context, chat_id, auction)) 
        end_task = asyncio.create_task(schedule_auction_end(context, chat_id, auction))  

        scheduled_tasks.setdefault(chat_id,{})[auction.id] = { 
            "start_task": start_task,           
            "end_task": end_task,               
        }

        await update.message.reply_text(
            f"🟢 Аукцион на {title}  (по МСК)\n\n"
            f"📅 Дата: {datetime.strptime(date_str, "%Y-%m-%d").strftime("%d/%m/%Y")}\n\n"
            f"🕘 Начало аукциона и конец аукциона: {start_time_str} - {end_time_str} (по МСК)\n\n"
            f"💰 Стартовая ставка: {start_bid} руб\n\n"
            f"🔁 Шаг ставки: {step} руб",
            )
        
    #Обработка ошибки
    except Exception as e: 
        await update.message.reply_text(f"❌ Ошибка при запуске аукциона: {e}")

#Проверка - какие аукционы есть в этом чате
@admin_only
async def show_aucs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать список активных и будущих аукционов"""
    print("📥 show_aucs вызван")  #вывод в консоль
    #Показать список активных и будущих аукционов
    chat_id = update.effective_chat.id
    now_time = datetime.now(ZoneInfo("Europe/Moscow"))

    # Проверяем, есть ли вообще аукционы в этом чате
    if chat_id not in auction_data or not auction_data[chat_id]:
        await update.message.reply_text("❌ Нет аукционов в этом чате.")
        return

    # Удаляем завершённые, перемещая их в архи
    future_aucs = []

    for auc in auction_data[chat_id]:
        if auc.end_dt < now_time:
            archived_auctions.setdefault(chat_id, []).append(auc)
        else:
            future_aucs.append(auc)
    auction_data[chat_id]= future_aucs

    # Перебираем ВСЕ аукционы — и активные, и будущие, и завершённые
    for i, auc in enumerate(auction_data[chat_id], start=1):
        # Определяем статус — активен или закрыт
        status = "✅ Активен" if auc.is_active else "❌ Закрыт/Отменён"

        # Текст сообщения
        text = (
            f"*🔹 Аукцион {i} — {status}*\n"
            f"📦 Лот: {auc.title}\n"
            f"📅 Дата: {auc.start_dt.strftime('%d-%m-%Y')}\n"
            f"⏰ Время начала и конца: {auc.start_dt.strftime('%H:%M')} - {auc.end_dt.strftime('%H:%M')}\n"
            f"💰 Старт: {auc.start_bid} руб | Шаг: {auc.step} руб"
        )

        # Кнопка для удаления аукциона по его ID
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🗑 Удалить", callback_data=f"delete_auc_{auc.id}")]
        ])

        # Отправляем сообщение в чат
        await update.message.reply_text(text,reply_markup=keyboard)  

@admin_only
async def delete_auc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удаление аукциона по номеру"""
    chat_id = update.effective_chat.id

    if chat_id not in auction_data or not auction_data[chat_id]:
        await update.message.reply_text("❌ Нет аукционов в этом чате.")
        return
    
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text(
            "⚠️ Укажи номер аукциона, например:\n\n"
            "`/delete_auc 2`", 
            )
        return
    
    index = int(context.args[0]) - 1

    if index < 0 or index >= len(auction_data[chat_id]):
        await update.message.reply_text("❌ Аукциона с таким номером не существует.")
        return
    
    auc = auction_data[chat_id].pop(index)

    if chat_id in scheduled_tasks and auc.id in scheduled_tasks[chat_id]:
        for task in scheduled_tasks[chat_id][auc.id].values():
            if not task.done():
                task.cancel()
        del scheduled_tasks[chat_id][auc.id]

    delete_auction(auc.id)
    await update.message.reply_text(f"🗑 Удалён аукцион «{auc.title}».")
    