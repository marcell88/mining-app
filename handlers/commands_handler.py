# handlers/commands_handler.py
from telegram import Update
from telegram.ext import ContextTypes
from services.database_service import get_stats, reset_stats
from config.settings import LOGGING_CHAT_ID # Используем LOGGING_CHAT_ID для фильтрации команд

async def handle_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает команду /stats.
    Отправляет пользователю статистику по входящим/исходящим сообщениям
    (общее количество и за последние 24 часа).
    """
    # Проверяем, что команда пришла от пользователя, который имеет право ее использовать,
    # например, из LOGGING_CHAT_ID, если это чат для администрирования.
    # Если LOGGING_CHAT_ID не установлен или команда пришла не из него,
    # можно отправить сообщение об ошибке или проигнорировать.
    if LOGGING_CHAT_ID and str(update.effective_chat.id) != LOGGING_CHAT_ID:
        await update.message.reply_text("Эта команда доступна только в чате логирования.")
        return
    
    stats = get_stats()
    
    response_text = (
        "📊 *Статистика сообщений:*\n\n"
        "*Общая статистика:*\n"
        f"  Входящих сообщений: `{stats['total_incoming']}`\n"
        f"  Исходящих сообщений (переслано): `{stats['total_outgoing']}`\n"
        f"  Процент пересылки: `{stats['total_percentage']:.2f}%`\n\n"
        "*За последние 24 часа:*\n"
        f"  Входящих сообщений: `{stats['last_24h_incoming']}`\n"
        f"  Исходящих сообщений (переслано): `{stats['last_24h_outgoing']}`\n"
        f"  Процент пересылки: `{stats['last_24h_percentage']:.2f}%`"
    )
    
    await update.message.reply_text(response_text, parse_mode='MarkdownV2')
    print(f"Статистика отправлена пользователю {update.effective_user.id}.")

async def handle_zero_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает команду /zero.
    Полностью обнуляет все счетчики сообщений в базе данных.
    """
    # Проверяем, что команда пришла от пользователя, который имеет право ее использовать.
    if LOGGING_CHAT_ID and str(update.effective_chat.id) != LOGGING_CHAT_ID:
        await update.message.reply_text("Эта команда доступна только в чате логирования.")
        return

    reset_stats()
    await update.message.reply_text("Все счетчики сообщений сброшены до нуля\\.")
    print(f"Счетчики сброшены пользователем {update.effective_user.id}.")

