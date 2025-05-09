from collections import defaultdict

auction_data = defaultdict(list)
archived_auctions = {}

# Планировщик задач: хранение отложенных запусков/завершений
# Формат: {chat_id: {auction_id: {"start_task": task, "end_task": task}}}
scheduled_tasks = {} # {chat_id: {auction_id: {"start_task": task, "end_task": task}}}
