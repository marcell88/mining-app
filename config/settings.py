# config/settings.py
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

# Получаем токен основного Telegram-бота из переменных окружения
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Получаем Chat ID приватной группы из переменных окружения
# Важно: Chat ID группы обычно начинается с минуса (например, -1234567890)
PRIVATE_GROUP_CHAT_ID = os.getenv("PRIVATE_GROUP_CHAT_ID")

# Получаем API ключ Deepseek
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# Получаем токен бота для логирования
LOGGING_BOT_TOKEN = os.getenv("LOGGING_BOT_TOKEN")

# Получаем Chat ID для логирования
LOGGING_CHAT_ID = os.getenv("LOGGING_CHAT_ID")

# Порог для второго этапа фильтрации Deepseek
CONTEXT_THRESHOLD = int(os.getenv("CONTEXT_THRESHOLD", 6))

# Новые константы для финальной фильтрации
MAX_POTENTIAL = int(os.getenv("MAX_POTENTIAL", 8)) # Порог для одной из оценок (эмоции, образность и т.д.)
SUM_POTENTIAL = float(os.getenv("SUM_POTENTIAL", 6.5)) # Порог для суммы всех 5 оценок


# Проверяем, что все необходимые переменные загружены
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("Переменная окружения TELEGRAM_BOT_TOKEN не установлена.")
if not PRIVATE_GROUP_CHAT_ID:
    raise ValueError("Переменная окружения PRIVATE_GROUP_CHAT_ID не установлена.")
if not LOGGING_BOT_TOKEN:
    print("Внимание: Переменная окружения LOGGING_BOT_TOKEN не установлена. Функционал команд /stats и /zero будет недоступен.")
if not LOGGING_CHAT_ID:
    print("Внимание: Переменная окружения LOGGING_CHAT_ID не установлена. Логирование в отдельный чат может быть недоступно.")

if not DEEPSEEK_API_KEY:
    print("Внимание: Переменная окружения DEEPSEEK_API_KEY не установлена. Функционал Deepseek может быть ограничен.")

