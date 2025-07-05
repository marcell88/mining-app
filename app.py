# app.py
from telegram.ext import Application, MessageHandler, filters, CommandHandler
from telegram import Update
from config.settings import TELEGRAM_BOT_TOKEN, PRIVATE_GROUP_CHAT_ID # LOGGING_BOT_TOKEN больше не используется здесь
from handlers.message_handler import handle_message, handle_stats_command, handle_zero_command
import asyncio # Импорт asyncio остается, если в handle_message есть await

def main():
    """Запускает Telegram-бота."""
    # Проверяем, что токен бота и ID группы установлены
    if not TELEGRAM_BOT_TOKEN:
        print("Ошибка: Токен основного Telegram-бота не найден. Убедитесь, что он указан в файле .env")
        return
    if not PRIVATE_GROUP_CHAT_ID:
        print("Ошибка: Chat ID приватной группы не найден. Убедитесь, что он указан в файле .env")
        return

    print("Инициализация Telegram-бота (основной бот)...")
    # Создаем объект Application для основного бота
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    print("Основной бот инициализирован.")

    # Регистрируем обработчик для текстовых сообщений (кроме команд)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Обработчик текстовых сообщений зарегистрирован.")

    # Регистрируем обработчик для команды /stats
    application.add_handler(CommandHandler("stats", handle_stats_command))
    print("Обработчик команды /stats зарегистрирован.")

    # Регистрируем обработчик для команды /zero
    application.add_handler(CommandHandler("zero", handle_zero_command))
    print("Обработчик команды /zero зарегистрирован.")

    print("Запуск прослушивания новых сообщений (polling)...")
    # Запускаем бота в режиме polling. Он будет периодически проверять новые сообщения.
    # run_polling() блокирует выполнение до остановки бота
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        print(f"Ошибка при запуске polling: {e}")
    finally:
        print("Бот остановлен.")

if __name__ == '__main__':
    # Запускаем основную функцию
    main()

