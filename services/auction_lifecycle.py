import asyncio
import random
from datetime import datetime
from data.storage import auction_data
from data.models import Auction
from utils.helpers import escape_markdown
from data.database import update_auction, get_all_auctions
from zoneinfo import ZoneInfo



START_PHRASES = ["ПОЕХАЛИ!", "НАЧАЛИ!", "СТАРТ!", "ПОНЕСЛАСЬ!", "ПОГНАЛИ!"]
STOP_PHRASE = ("⛔️ СТОП!\n\n Аукцион - ЗАВЕРШЕН.")

async def schedule_auction_start(context, chat_id: int, auction: Auction):
    """Планирует и запускает аукцион в указанное время"""

    print(f"▶️ Задача на запуск аукциона запланирована: {auction.title}")
    # Определяем разницу между текущим временем и временем старта
    now = datetime.now(tz=auction.start_dt.tzinfo)  # всегда МСК!
    delay = (auction.start_dt - now).total_seconds()

    # Ждём нужное количество секунд
    await asyncio.sleep(max(0, delay))

    # Запуск аукциона
    await start_auction(context, chat_id, auction)


async def start_auction(context, chat_id: int, auction: Auction):
    """Запускает аукцион — изменяет статус и отправляет стартовое сообщение"""
    print(f"🎯 start_auction запущен для {auction.title}")

    #1. Провека, наличия чата в объекте аукционов
    if chat_id not in auction_data:
        return 
    
    # 2. Проверяем, есть ли аукцион по его ID
    existing_auction = next((a for a in auction_data[chat_id] if a.id == auction.id), None)

    if not existing_auction or not existing_auction.is_active:
        return
    
    existing_auction.is_running = True  #Статус аукциона активен или нет
    existing_auction.is_paused = False
    existing_auction.invalid_count = 0 #Счетчик ошибок
    existing_auction.all_bids = []

    phrase = random.choice(START_PHRASES)

    await context.bot.send_message(
        chat_id,
        f"📢 {phrase}\n\n💰 НАЧАЛЬНАЯ СТАВКА: {existing_auction.start_bid} РУБ. \n\n"
        f"👟  ШАГ: {existing_auction.step}",
    )   


async def schedule_auction_end(context, chat_id: int, auction: Auction):
    """Планирует завершение аукциона"""
    now = datetime.now(tz=auction.end_dt.tzinfo)
    delay = (auction.end_dt - now).total_seconds()

    # Ждём окончания
    await asyncio.sleep(max(0, delay))

    # Завершаем аукцион
    await stop_auction(context, chat_id, auction)


async def stop_auction(context, chat_id: int, auction: Auction):
    """Завершает аукцион, объявляет победителя или пишет, что ставок не было"""
    print(f'Stop auction')
   
    current_auction = next((a for a in auction_data.get(chat_id, []) if a.id == auction.id), None)
    if not current_auction:
        print("❌ Не найден аукцион в памяти")
        return

    if not current_auction.is_active or current_auction.is_finish:
        print(f' Пропущено завершение аукциона {current_auction.title} — он уже неактивен')
        return
    
    if current_auction.all_bids:
        # Берем последнюю ставку (она же и победитель)
        last_bid = current_auction.all_bids[-1]
        user = last_bid['user']
        amount = str(last_bid['bid'])
        # user, amount = auction["all_bids"][-1]

        user = escape_markdown(user)
        amount = escape_markdown(str(amount))

        final_msg = (
            f"{STOP_PHRASE}\n\n"
            f"🏆 Победитель аукциона *{current_auction.title}*: {user}\n\n"
            f"💸 Ставка: {amount} руб\n\n"
            f"📩 Напиши нам @finka_nkvd_zakaz — оформим победу!"
        )

    else:
        final_msg = (
            f"{STOP_PHRASE}\n\n"
            f"Аукцион *{current_auction.title}* завершён ❌\n"
            f"Ставок не было."
        )

    await context.bot.send_message(
        chat_id=chat_id,
        text=final_msg,
    )
        
    current_auction.is_running = False  # Отключаем приём ставок
    current_auction.is_finish = True    # Ставим завершение
    current_auction.is_active = False

    update_auction(current_auction)

    asyncio.create_task(schedule_memory_cleanup(chat_id, current_auction.id))


async def schedule_memory_cleanup (chat_id: int, auction_id: str, delay: float = 360):
    #  """
    # Удаляет завершённый аукцион из памяти через `delay` секунд (по умолчанию 10 минут)
    # """
    await asyncio.sleep(delay)

    if chat_id not in auction_data:
        return

    auctions = auction_data[chat_id]
    before = len(auctions)
    auction_data[chat_id] = [a for a in auctions if a.id != auction_id]
    after = len(auction_data[chat_id])

    print(f"🧹 Очистка памяти: удалён аукцион {auction_id} из chat_id={chat_id} ({before} → {after}. Переменная аукциона {auction_data[chat_id]})")


async def restore_scheduled_tasks(application):
    """Восстанавливает незавершённые аукционы из БД при запуске бота"""
    all_auctions = get_all_auctions()
    now = datetime.now(ZoneInfo("Europe/Moscow"))

    for auction in all_auctions:
        if auction.is_active and not auction.is_finish:
            # auction_data[auction.chat_id] = []
            auction_data.setdefault(auction.chat_id, [])

            if not any(a.id == auction.id for a in auction_data[auction.chat_id]):
                auction_data[auction.chat_id].append(auction)
            
            if auction.start_dt > now:
                print(f"⏳ Восстановление задачи запуска для: {auction.title}")
                asyncio.create_task(schedule_auction_start(application, auction.chat_id, auction))
            
            elif auction.start_dt <= now <= auction.end_dt:
                print(f"🔥 Аукцион уже должен идти: {auction.title} — запускаем немедленно")
                asyncio.create_task(schedule_auction_start(application, auction.chat_id, auction))

            if auction.end_dt > now:
                print(f"📌 Планируем завершение для: {auction.title}")
                asyncio.create_task(schedule_auction_end(application, auction.chat_id, auction))
