# logging_bot_app.py
from telegram.ext import Application, CommandHandler
from telegram import Update
from config.settings import LOGGING_BOT_TOKEN
from handlers.message_handler import handle_stats_command, handle_zero_command # Только обработчики команд

def main():
    """Запускает Telegram-бот для логирования и статистики."""
    if not LOGGING_BOT_TOKEN:
        print("Ошибка: Токен бота для логирования не найден. Убедитесь, что он указан в файле .env")
        return

    print("Инициализация бота для логирования...")
    application = Application.builder().token(LOGGING_BOT_TOKEN).build()
    print("Бот для логирования инициализирован.")

    # Регистрируем обработчики команд /stats и /zero
    application.add_handler(CommandHandler("stats", handle_stats_command))
    print("Обработчик команды /stats для бота логирования зарегистрирован.")
    application.add_handler(CommandHandler("zero", handle_zero_command))
    print("Обработчик команды /zero для бота логирования зарегистрирован.")

    print("Запуск прослушивания новых сообщений для бота логирования (polling)...")
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        print(f"Ошибка при запуске бота для логирования: {e}")
    finally:
        print("Бот для логирования остановлен.")

if __name__ == '__main__':
    main()

