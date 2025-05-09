import os
import shutil
from datetime import datetime

DB_SOURCE = 'data/aucbot.db'

BACKUP_DIR = "backup"

def make_backup():
    """
    Создаёт резервную копию файла базы данных:
    - Копирует `data/aucbot.db` в папку `backup/`
    - Присваивает файлу имя с текущей датой и временем
      (например: aucbot_01-05-2025_02-00-00.db)
    """

    if not os.path.exists(DB_SOURCE):
        print("❌ База данных не найдена — резервное копирование невозможно.")
        return
    
    os.makedirs(BACKUP_DIR, exist_ok=True)

    now_time = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")

    backup_filename = f"aucbot_{now_time}.db"

    backup_path = os.path.join(BACKUP_DIR, backup_filename)

    try:
        shutil.copy(DB_SOURCE, backup_path)
        print(f'✅Резервная копия создана: {backup_path}')
    except Exception as e: 
         print(f"❌ Ошибка при создании резервной копии: {e}")