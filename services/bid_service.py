import random
import asyncio
from utils.helpers import escape_markdown
from telegram import Update
from telegram.ext import ContextTypes
from data.storage import auction_data
from data.database import update_auction
from utils.helpers import extract_first_number, format_timestamp


async def process_user_bid_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает входящее сообщение от пользователя и интерпретирует его как ставку,
    если сейчас идёт активный аукцион в этом чате.
    """
    chat_id = update.effective_chat.id
    message = update.message

    if chat_id not in auction_data:
        return 

    auctions = auction_data[chat_id]

    # Находим один активный и запущенный аукцион
    current_auc = next(
        (a for a in auctions if a.is_active and a.is_running and not a.is_finish),
        None
    )
    
    if not current_auc or current_auc.is_paused:
        return
 
    bid = extract_first_number(message.text)
    if bid is None:
        return

    # username = update.effective_user.username or update.effective_user.first_name
    user_obj = update.effective_user
    if user_obj.username:
        username = f"@{user_obj.username}"
    else:
        username = user_obj.first_name

    last = current_auc.last_valid_bid
    step = current_auc.step

    timestamp = format_timestamp(message.date)

    # Запоминаем попытку (правильную или нет)
    bet_record = {
        'user': username,
        'bid': bid,
        'time': timestamp
    }
    current_auc.all_bets_placed.append(bet_record)

    if bid == last + step:

        current_auc.last_valid_bid = bid
        current_auc.all_bids.append(bet_record)
        current_auc.invalid_count = 0

        print (f'СТАВКИ - {current_auc.all_bids}')
        return

    else:
    # ❌ Некорректная ставка
        current_auc.invalid_count += 1

        if current_auc.invalid_count  >= 5:
            current_auc.is_paused = True

            await context.bot.send_message(chat_id=chat_id, text="⏸ ПАУЗА, СЛИШКОМ МНОГО НЕВЕРНЫХ СТАВОК")

            # Подождём от 1 до 4 секунд
            asyncio.create_task(resume_after_pause(context, chat_id, current_auc))
            return
        
    update_auction(current_auc)

async def resume_after_pause(context, chat_id, auction):
    await asyncio.sleep(random.randint(1, 4))

    if auction.is_finish:
        return

    phrase = random.choice(["Продолжаем", "Погнали", "Поехали"])

    if auction.all_bids:
        last_bid = auction.all_bids[-1]
        user = last_bid['user']
        amount = last_bid['bid']

        # Если username уже начинается с @ — оставляем, иначе экранируем имя
        if user.startswith("@"):
            user_display = user
        else:
            user_display = escape_markdown(user)  # Экранируем для Markdown

        msg = f"▶️ {phrase}! Последняя ставка: {amount} от {user_display}"
    else:
        msg = f"▶️ {phrase}! Пока ещё нет ни одной ставки."

    await context.bot.send_message(
        chat_id=chat_id,
        text=msg
    )

    auction.is_paused = False
    auction.invalid_count = 0

    update_auction(auction)  #обновляем данные в БД
