# handlers/commands_handler.py
from telegram import Update
from telegram.ext import ContextTypes
from services.database_service import get_stats, reset_stats

async def handle_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает команду /stats.
    Отправляет пользователю текущую статистику входящих и исходящих сообщений.
    """
    incoming, outgoing = get_stats()
    
    percentage = 0.0
    if incoming > 0:
        percentage = (outgoing / incoming) * 100

    response_text = (
        f"Текущая статистика:\n"
        f"Входящих сообщений: {incoming}\n"
        f"Исходящих сообщений: {outgoing}\n"
        f"Процент исходящих к входящим: {percentage:.2f}%"
    )
    await update.message.reply_text(response_text)
    print(f"Команда /stats выполнена. Статистика отправлена пользователю {update.message.chat_id}.")


async def handle_zero_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает команду /zero.
    Обнуляет счетчики входящих и исходящих сообщений в базе данных.
    """
    reset_stats()
    await update.message.reply_text("Счетчики входящих и исходящих сообщений сброшены до нуля.")
    print(f"Команда /zero выполнена. Счетчики сброшены пользователем {update.message.chat_id}.")

