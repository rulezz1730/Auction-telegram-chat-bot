from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class Auction:
    
    # Модель аукциона для хранения данных в оперативной памяти и базе данных
    id: str                          # Уникальный идентификатор UUID
    chat_id: str                     # ID Telegram-чата, где проходит аукцион
    title: str                       # Название или описание лота
    start_dt: datetime               # Дата и время начала
    end_dt: datetime                 # Дата и время завершения
    start_bid: int                   # Начальная ставка
    step: int                        # Шаг ставки
    is_active: bool                  # True — активен, False — удалён или завершён
    is_running: bool                # True — сейчас идёт, False — ещё не начался или уже завершён
    is_finish: bool                 # True — завершён
    last_valid_bid: int              # Последняя корректная ставка
    invalid_count: int = 0           # Кол-во неверных подряд ставок
    can_count_invalid: bool = True   # Разрешено ли считать неправильные ставки
    is_paused: bool = False          # Находится ли аукцион на паузе
    all_bids: List[Dict] = field(default_factory=list)  # Только корректные ставки [{'user': ..., 'bid': ..., 'time': ...}]
    all_bets_placed: List[Dict] = field(default_factory=list)  # Все ставки [{'user': ..., 'bid': ..., 'time': ...}]