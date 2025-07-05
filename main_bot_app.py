# main_bot_app.py
from telegram.ext import Application, MessageHandler, filters
from telegram import Update
from config.settings import TELEGRAM_BOT_TOKEN, PRIVATE_GROUP_CHAT_ID
from handlers.message_handler import handle_message # Только обработчик сообщений

def main():
    """Запускает основной Telegram-бот."""
    if not TELEGRAM_BOT_TOKEN:
        print("Ошибка: Токен основного Telegram-бота не найден. Убедитесь, что он указан в файле .env")
        return
    if not PRIVATE_GROUP_CHAT_ID:
        print("Ошибка: Chat ID приватной группы не найден. Убедитесь, что он указан в файле .env")
        return

    print("Инициализация основного Telegram-бота...")
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    print("Основной бот инициализирован.")

    # Регистрируем только обработчик текстовых сообщений (кроме команд)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Обработчик текстовых сообщений для основного бота зарегистрирован.")

    print("Запуск прослушивания новых сообщений для основного бота (polling)...")
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        print(f"Ошибка при запуске основного бота: {e}")
    finally:
        print("Основной бот остановлен.")

if __name__ == '__main__':
    main()

