# services/telegram_logger.py
from telegram import Bot
from telegram.constants import ParseMode # Исправлено: теперь импортируем ParseMode из telegram.constants
import html
from config.settings import LOGGING_BOT_TOKEN, LOGGING_CHAT_ID

# Инициализируем Bot для логирования один раз при загрузке модуля
logging_bot = None
if LOGGING_BOT_TOKEN:
    try:
        logging_bot = Bot(token=LOGGING_BOT_TOKEN)
        print("Бот для логирования успешно инициализирован в telegram_logger.")
    except Exception as e:
        print(f"Ошибка при инициализации бота для логирования в telegram_logger: {e}")
else:
    print("Внимание: LOGGING_BOT_TOKEN не установлен, логирование в отдельный бот будет недоступно.")

async def send_log_message(
    main_message: str,
    message_link: str,
    filter_value_1: str,
    explain_value_1: str,
    filter_value_2: str,
    total_score_context: int,
    explain_value_2: str,
    final_filter_value: str,
    total_potential_score: int,
    emotion_score: int,
    emotion_explain: str,
    image_score: int,
    image_explain: str,
    humor_score: int,
    humor_explain: str,
    surprise_score: int,
    surprise_explain: str,
    drama_score: int,
    drama_explain: str,
    is_filtered_by_stage_2: bool
) -> None:
    """
    Отправляет лог-сообщение в отдельный Telegram-бот.
    Текст сообщения форматируется без жирного выделения и с учетом ваших стилистических предпочтений.
    """
    if logging_bot and LOGGING_CHAT_ID:
        # Убедимся, что все explain_value_X являются строками перед экранированием
        escaped_main_message = html.escape(main_message)
        escaped_message_link = html.escape(message_link)
        escaped_filter_value_1 = html.escape(filter_value_1)
        escaped_explain_value_1 = html.escape(str(explain_value_1))
        escaped_filter_value_2 = html.escape(filter_value_2)
        escaped_total_score_context = html.escape(str(total_score_context))
        escaped_explain_value_2 = html.escape(str(explain_value_2))

        # Экранированные значения для оценок характеристик (только баллы, без объяснений)
        escaped_emotion_score = html.escape(str(emotion_score))
        escaped_image_score = html.escape(str(image_score))
        escaped_humor_score = html.escape(str(humor_score))
        escaped_surprise_score = html.escape(str(surprise_score))
        escaped_drama_score = html.escape(str(drama_score))

        log_message_text = (
            f"Исходное сообщение:\n\n{escaped_main_message}\n\n"
            f"1111\n\n"
            f"Ссылка: {escaped_message_link}\n\n"
            f"1111\n\n"
            f"Фильтр Deepseek (Этап 1): {escaped_filter_value_1}\n"
            f"Context Filtration (Этап 2): {escaped_filter_value_2}\n"
            f"Сумма баллов (Этап 2): {escaped_total_score_context}\n\n"
        )
        
        # Добавляем оценки характеристик только если filter_value_2 был "Да"
        if is_filtered_by_stage_2:
            log_message_text += (
                f"--- Оценки характеристик ---\n"
                f"Эмоциональная яркость: {escaped_emotion_score}\n"
                f"Образность: {escaped_image_score}\n"
                f"Юмор: {escaped_humor_score}\n"
                f"Неожиданность: {escaped_surprise_score}\n"
                f"Драматичность: {escaped_drama_score}\n\n"
                f"Финальный фильтр: {html.escape(final_filter_value)}\n"
                f"Сумма потенциальных баллов: {html.escape(str(total_potential_score))}\n"
            )

        try:
            sent_message = await logging_bot.send_message(
                chat_id=LOGGING_CHAT_ID,
                text=log_message_text,
                parse_mode=ParseMode.HTML
            )
            log_message_id = sent_message.message_id
            print(f"Лог успешно отправлен ботом логирования в чат {LOGGING_CHAT_ID}. Message ID: {log_message_id}")
        except Exception as e:
            print(f"Ошибка при отправке лога ботом логирования в чат {LOGGING_CHAT_ID}: {e}")
    else:
        print("Бот для логирования или LOGGING_CHAT_ID не инициализирован, лог не отправлен.")

