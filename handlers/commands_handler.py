# handlers/commands_handler.py
from telegram import Update
from telegram.ext import ContextTypes
from services.database_service import get_stats, reset_stats
from config.settings import LOGGING_CHAT_ID
from telegram.constants import ParseMode # Import ParseMode

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
    
    # MarkdownV2 requires escaping of many characters:
    # _, *, [, ], (, ), ~, `, >, #, +, -, =, |, {, }, ., !
    # We want bolding for titles, so `*` is left unescaped for those parts.
    # We need to escape literal `(`, `)`, and `%` signs.
    
    response_text = (
        "📊 *Статистика сообщений:*\n\n"
        "*Общая статистика:*\n"
        f"  Входящих сообщений: `{stats['total_incoming']}`\n"
        f"  Исходящих сообщений \\(переслано\\): `{stats['total_outgoing']}`\n" # Escaped parentheses
        f"  Процент пересылки: `{stats['total_percentage']:.2f}\\%`\n\n"      # Escaped percentage sign
        "*За последние 24 часа:*\n"
        f"  Входящих сообщений: `{stats['last_24h_incoming']}`\n"
        f"  Исходящих сообщений \\(переслано\\): `{stats['last_24h_outgoing']}`\n" # Escaped parentheses
        f"  Процент пересылки: `{stats['last_24h_percentage']:.2f}\\%`"      # Escaped percentage sign
    )
    
    await update.message.reply_text(response_text, parse_mode=ParseMode.MARKDOWN_V2)
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
    # The existing `\.` is correct for MarkdownV2
    await update.message.reply_text("Все счетчики сообщений сброшены до нуля\\.", parse_mode=ParseMode.MARKDOWN_V2)
    print(f"Счетчики сброшены пользователем {update.effective_user.id}.")

