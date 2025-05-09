import sqlite3
import os
import json
from datetime import datetime
from data.models import Auction

DB_NAME = "data/aucbot.db"

# --- Инициализация базы данных ---
#     - Создание папки 'data', если её нет
#     - Создание файла базы 'aucbot.db', если его нет
#     - Создание таблицы 'auctions', если её нет
#----------------------------------

def init_db():
    os.makedirs(os.path.dirname(DB_NAME), exist_ok=True) # Создание папки data/ если нет

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS auctions (
        id TEXT PRIMARY KEY,
        chat_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        start_dt TEXT NOT NULL,
        end_dt TEXT NOT NULL,
        start_bid INTEGER NOT NULL,
        step INTEGER NOT NULL,
        is_active INTEGER NOT NULL,
        is_running INTEGER NOT NULL,
        is_finish INTEGER NOT NULL,
        last_valid_bid INTEGER NOT NULL,
        invalid_count INTEGER NOT NULL,
        can_count_invalid INTEGER NOT NULL,
        is_paused INTEGER NOT NULL,
        all_bids TEXT NOT NULL,
        all_bets_placed TEXT NOT NULL
    )
    ''')

    conn.commit()
    conn.close()

def insert_auction(auction: Auction):
     # Добавление нового аукциона в БД
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # Вставка нового аукциона
        cursor.execute('''
        INSERT INTO auctions (
            id, chat_id, title, start_dt, end_dt, start_bid, step,
            is_active, is_running, is_finish,
            last_valid_bid, invalid_count, can_count_invalid, is_paused,
            all_bids, all_bets_placed
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            auction.id,
            auction.chat_id,
            auction.title,
            auction.start_dt.isoformat(),  # Переводим datetime в строку ISO
            auction.end_dt.isoformat(),
            auction.start_bid,
            auction.step,
            int(auction.is_active),
            int(auction.is_running),
            int(auction.is_finish),
            auction.last_valid_bid,
            auction.invalid_count,
            int(auction.can_count_invalid),
            int(auction.is_paused),
            json.dumps(auction.all_bids, ensure_ascii=False),# Переводим список в строку JSON
            json.dumps(auction.all_bets_placed, default=str)
        ))

        conn.commit()
    except sqlite3.OperationalError as e:
        print("❌ SQLite ошибка:", e)
    finally:
        conn.close()

def get_all_auctions() -> list[Auction]:

    # Загрузка всех аукционов из базы данных
    # Возвращает список объектов Auction
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Выбираем все записи из таблицы 'auctions'
    cursor.execute('SELECT * FROM auctions')
    rows = cursor.fetchall()
    conn.close()

    auctions = []
    for row in rows:

        try:
            all_bids = json.loads(row[14])
        except json.JSONDecodeError:
            all_bids = []
        try:
            all_bets_placed = json.loads(row[15])
        except json.JSONDecodeError:
            all_bets_placed = []

        auctions.append(Auction(
            id=row[0],
            chat_id=row[1],
            title=row[2],
            start_dt=datetime.fromisoformat(row[3]),  # Переводим строку ISO обратно в datetime
            end_dt=datetime.fromisoformat(row[4]),
            start_bid=row[5],
            step=row[6],
            is_active=bool(row[7]),
            is_running=bool(row[8]),
            is_finish=bool(row[9]),
            last_valid_bid=row[10],
            invalid_count=row[11],
            can_count_invalid=bool(row[12]),
            is_paused=bool(row[13]),
            all_bids=json.loads(row[14]),           # Переводим JSON-строку обратно в список
            all_bets_placed=json.loads(row[15])
        ))
    return auctions  

def update_auction(auction: Auction):
    print(f"📝 ОБНОВЛЯЕМ АУКЦИОН {auction.title}")

    # Обновление существующего аукциона в базе данных
    # Сохраняем текущее состояние аукциона после изменения ставок, паузы, завершения
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Обновляем поля существующего аукциона
    cursor.execute('''
    UPDATE auctions
    SET
        is_active = ?,
        is_running = ?,
        is_finish = ?,
        last_valid_bid = ?,
        invalid_count = ?,
        can_count_invalid = ?,
        is_paused = ?,
        all_bids = ?,
        all_bets_placed = ?
    WHERE id = ?
    ''', (
        int(auction.is_active),
        int(auction.is_running),
        int(auction.is_finish),
        auction.last_valid_bid,
        auction.invalid_count,
        int(auction.can_count_invalid),
        int(auction.is_paused),
        json.dumps(auction.all_bids, ensure_ascii=False),           # Сохраняем списки в JSON-строку
        json.dumps(auction.all_bets_placed, ensure_ascii=False),
        auction.id
    ))

    conn.commit()
    conn.close()     

def delete_auction(auction_id: str):
    # Удаление одного аукциона из базы данных по его уникальному ID
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Удаляем запись по ID
    cursor.execute('DELETE FROM auctions WHERE id = ?', (auction_id,))
    conn.commit()
    conn.close() 

