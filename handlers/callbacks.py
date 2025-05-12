from utils.decorators import admin_only
from telegram import Update
from telegram.ext import ContextTypes
from data.storage import auction_data, scheduled_tasks
from data.database import delete_auction
import pprint

# Колбэк на удаление аукциона
@admin_only
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка callback-кнопки удаления аукциона"""
    query = update.callback_query # объект с информацией о нажатой кнопке
    await query.answer() #Закрываем часы у пользователя это требует Телеграмм
    
    chat_id = query.message.chat.id
    data = query.data

    if data.startswith('delete_auc_'): # то, что мы передали как callback_data (например: "delete_auc_2")
        auc_id = data.replace("delete_auc_", "")

        if chat_id not in auction_data:
            await query.edit_message_text("❌ Аукцион не найден.")
            return
        
        for i, auc in enumerate(auction_data[chat_id]):
            if auc.id == auc_id:
                removed_auc = auction_data[chat_id].pop(i)

                if chat_id in scheduled_tasks and auc_id in scheduled_tasks[chat_id]:
                    tasks = scheduled_tasks[chat_id][auc_id]
                    for task in tasks.values():
                        if not task.done():
                            try:
                                task.cancel()
                            except Exception as e:
                                print(f"❗ Ошибка при отмене задачи: {e}")
                    del scheduled_tasks[chat_id][auc_id]

                delete_auction(auc_id)

                await query.edit_message_text(
                    f"🗑 Аукцион «{removed_auc.title}» удалён.",
                    )
                
                print("\n📦 Состояние auction_data после удаления:")
                pprint.pprint(auction_data.get(chat_id, []), indent=2)

                print("\n🕑 Состояние scheduled_tasks после удаления:")
                pprint.pprint(scheduled_tasks.get(chat_id, {}), indent=2)

                return
            
            
        await query.edit_message_text("❌ Аукцион уже удалён или не найден.")