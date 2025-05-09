import re
from zoneinfo import ZoneInfo
from data.storage import auction_data
from datetime import datetime

# Вспомогательная функция — извлекает первое число из текста сообщения
def extract_first_number(text: str) -> int | None:
    """
    Извлекает первое положительное целое число из текста.
    Возвращает None, если числа нет.
    """
    match = re.search(r'\d+', text) # Находим первое вхождение числа
    if match: #Условие, если есть совпадение
        return int(match.group()) 
    return None

def escape_markdown(text: str) -> str:
    """ 
    Для Markdown дополняет слешами перед символами. 
    Я решил отказаться от этого, слишком много подводных камней и для V1 и для V2
    """
    special_cahrs = r"_*[]()~`>#+-=|{}.!\\"
    for char in special_cahrs: 
        text = text.replace(char, f"\\{char}")
    return text

def title_parser_new_auc(args: list):
    """
    Разбирает аргументы команды /new_auc на составляющие:
    - title
    - date_str
    - start_time_str
    - end_time_str
    - start_bid_str
    - step_str
    Возвращает словарь или None если ошибка.
    """
    if not args:
        return None
    
    # ищем индекс первой даты в формате ГГГГ-ММ-ДД
    date_index = next((i for i, arg in enumerate(args) if re.match(r"\d{4}-\d{2}-\d{2}", arg)), None)


    if date_index is None or len(args) - date_index < 5:
        return None
    
    print(f"ТЕКСТ - {" ".join(args[:date_index]),}")
    print(f"Дата  - {args[date_index]}")
    print(f"Время начала  - {args[date_index + 1]}")
    print(f"Время конца  - {args[date_index + 2]}")

    title = " ".join(args[:date_index])
    date_str = args[date_index]
    start_time_str = args[date_index + 1]
    end_time_str = args[date_index + 2]
    start_bid_str = args[date_index + 3]
    step_str = args[date_index + 4]

    return title, date_str, start_time_str, end_time_str, start_bid_str, step_str


def check_overlap(chat_id: int, start_dt: datetime, end_dt: datetime) -> tuple[bool, dict]:
    """
    Проверяет, пересекается ли новый аукцион по времени с уже существующими активными аукционами.
    :param chat_id: ID чата
    :param start_dt: datetime начала нового аукциона
    :param end_dt: datetime окончания нового аукциона
    :return: (True, существующий аукцион) если пересечение найдено, иначе (False, None)
    """
    if chat_id not in auction_data:
        return False, None

    for existing_auc in auction_data[chat_id]:
        if existing_auc.is_active:
            existing_start = existing_auc.start_dt
            existing_end = existing_auc.end_dt

            # Проверяем: дата совпадает И пересекаются времена
            if start_dt.date() == existing_start.date():
                if start_dt < existing_end and existing_start < end_dt:
                    return True, existing_auc

    return False, None

def format_timestamp(dt: datetime) -> str:
    """
    Обработка времени в удобный формат
    """
    return dt.astimezone(ZoneInfo("Europe/Moscow")).strftime("%H:%M:%S, %d-%m-%Y")