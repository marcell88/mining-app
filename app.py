# app.py
import asyncio
from telegram.ext import Application, MessageHandler, filters, CommandHandler
from telegram import Update # Bot больше не нужно импортировать явно здесь
from config.settings import TELEGRAM_BOT_TOKEN, PRIVATE_GROUP_CHAT_ID, LOGGING_BOT_TOKEN, LOGGING_CHAT_ID
from handlers.message_handler import handle_message
from handlers.commands_handler import handle_stats_command, handle_zero_command
# from services.telegram_logger import logging_bot as telegram_logger_bot # Больше не нужен прямой импорт глобального бота здесь

async def main():
    """Запускает объединенного Telegram-бота."""
    # Проверяем, что токены и ID группы установлены
    if not TELEGRAM_BOT_TOKEN:
        print("Ошибка: Токен основного Telegram-бота не найден. Убедитесь, что он указан в файле .env")
        return
    if not PRIVATE_GROUP_CHAT_ID:
        print("Ошибка: Chat ID приватной группы не найден. Убедитесь, что он указан в файле .env")
        return
    # LOGGING_BOT_TOKEN и LOGGING_CHAT_ID проверяются внутри telegram_logger.py
    # и их отсутствие не должно прерывать работу основного бота.

    print("Инициализация Telegram-бота...")
    # Создаем один объект Application для всего бота
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    print("Бот инициализирован.")

    try:
        print("Вызов initialize() для бота...")
        await application.initialize()
        print("Бот инициализирован успешно.")
    except Exception as e:
        print(f"Ошибка при инициализации бота: {e}")
        return

    # Регистрируем обработчик для текстовых сообщений (НЕ команд)
    # Это предотвратит обработку команд как обычных сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Обработчик текстовых сообщений зарегистрирован (исключая команды).")

    # Регистрируем обработчики команд /stats и /zero
    # Эти обработчики будут реагировать только на команды с соответствующим именем
    application.add_handler(CommandHandler("stats", handle_stats_command))
    print("Обработчик команды /stats зарегистрирован.")
    application.add_handler(CommandHandler("zero", handle_zero_command))
    print("Обработчик команды /zero зарегистрирован.")

    print("Запуск прослушивания новых сообщений для бота...")
    try:
        # Запускаем один Application
        await application.start()
        print("Бот запущен.")
    except Exception as e:
        print(f"Ошибка при запуске бота: {e}")
        return

    print("Бот запущен. Ожидание сообщений...")
    # Эта строка будет держать цикл событий активным, пока бот работает.
    await asyncio.Future()

if __name__ == '__main__':
    try:
        # Запускаем асинхронную функцию main
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен пользователем.")
    except Exception as e:
        print(f"Произошла непредвиденная ошибка во время выполнения: {e}")

