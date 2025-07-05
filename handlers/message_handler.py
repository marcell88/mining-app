# handlers/message_handler.py
from telegram import Update, Bot
from telegram.ext import ContextTypes
from config.settings import PRIVATE_GROUP_CHAT_ID, LOGGING_BOT_TOKEN, LOGGING_CHAT_ID, CONTEXT_THRESHOLD, MAX_POTENTIAL, SUM_POTENTIAL
from services.database_service import increment_incoming_messages, increment_outgoing_messages, get_stats, reset_stats
from services.deepseek_service import initial_filtration
from prompts import (
    FILTER_INSTRUCTIONS,
    CONTEXT_FILTRATION_INSTRUCTIONS,
    EMOTION_INSTRUCTIONS,
    IMAGE_INSTRUCTIONS,
    HUMOR_INSTRUCTIONS,
    SURPRISE_INSTRUCTIONS,
    DRAMA_INSTRUCTIONS
)
from telegram.constants import ParseMode
import html
from datetime import datetime

# Инициализируем Bot для логирования один раз при загрузке модуля
logging_bot = None
if LOGGING_BOT_TOKEN:
    try:
        logging_bot = Bot(token=LOGGING_BOT_TOKEN)
        print("Бот для логирования успешно инициализирован в message_handler.")
    except Exception as e:
        print(f"Ошибка при инициализации бота для логирования в message_handler: {e}")
else:
    print("Внимание: LOGGING_BOT_TOKEN не установлен, логирование в отдельный бот будет недоступно.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обрабатывает входящие текстовые сообщения от пользователя.
    Инкрементирует счетчик входящих сообщений в SQLite.
    Разбивает сообщение на части (текст и ссылка).
    Проводит три этапа фильтрации с помощью Deepseek.
    Условно пересылает сообщение в приватную группу и инкрементирует счетчик исходящих,
    а также всегда отправляет лог в отдельный бот, сохраняя его message_id.
    """
    user_full_message = update.message.text
    chat_id = update.message.chat_id

    print(f"Получено сообщение от {chat_id}: {user_full_message}")

    increment_incoming_messages()

    if not user_full_message:
        print("Получено пустое сообщение.")
        return

    parts = user_full_message.split('1111\n\n')

    main_message = ""
    message_link = "Нет ссылки"
    
    if len(parts) >= 1:
        main_message = parts[0].strip()
    if len(parts) >= 2:
        message_link = parts[1].strip()

    # --- Первый этап фильтрации (Initial Filtration) ---
    deepseek_prompt_1 = f"Сообщение: {main_message}\nСсылка: {message_link}\n\n{FILTER_INSTRUCTIONS}"
    
    deepseek_response_schema_1 = {
        "type": "OBJECT",
        "properties": {
            "filter": {"type": "STRING", "enum": ["Да", "Нет"]},
            "explain": {"type": "STRING"}
        },
        "required": ["filter", "explain"]
    }

    print(f"Отправка запроса к Deepseek (этап 1) с промптом (часть): '{main_message[:50]}...'")
    deepseek_result_1 = initial_filtration(
        prompt=deepseek_prompt_1,
        response_schema=deepseek_response_schema_1
    )
    
    filter_value_1 = "Ошибка"
    explain_value_1 = "Не удалось получить объяснение от Deepseek (этап 1)."

    if isinstance(deepseek_result_1, dict):
        filter_value_1 = deepseek_result_1.get("filter", "Ошибка")
        explain_value_1 = deepseek_result_1.get("explain", "Не удалось получить объяснение (этап 1).")
        print(f"Получен структурированный ответ от Deepseek (этап 1): Filter='{filter_value_1}', Объяснение='{str(explain_value_1)[:50]}...'")
    else:
        print(f"Ошибка при получении структурированного ответа от Deepseek (этап 1): {deepseek_result_1}")
        explain_value_1 = str(deepseek_result_1) # Убедимся, что explain_value_1 всегда строка
    # --- Конец первого этапа фильтрации ---

    # --- Второй этап фильтрации (Context Filtration, если первый этап вернул "Да") ---
    filter_value_2 = "Нет" # По умолчанию "Нет" для второго этапа
    total_score_context = 0
    explain_value_2 = "Второй этап фильтрации не проводился (первый этап вернул 'Нет')."

    if filter_value_1 == "Да":
        current_date = datetime.now().strftime("%Y-%m-%d")
        deepseek_prompt_2 = f"Текущая дата: {current_date}\nСообщение: {main_message}\n\n{CONTEXT_FILTRATION_INSTRUCTIONS}"

        deepseek_response_schema_2 = {
            "type": "OBJECT",
            "properties": {
                "subject": {"type": "INTEGER", "minimum": 0, "maximum": 10},
                "object": {"type": "INTEGER", "minimum": 0, "maximum": 10},
                "which": {"type": "INTEGER", "minimum": 0, "maximum": 10},
                "action": {"type": "INTEGER", "minimum": 0, "maximum": 10},
                "time_place": {"type": "INTEGER", "minimum": 0, "maximum": 10},
                "how": {"type": "INTEGER", "minimum": 0, "maximum": 10},
                "reason": {"type": "INTEGER", "minimum": 0, "maximum": 10},
                "consequences": {"type": "INTEGER", "minimum": 0, "maximum": 10},
                "explain": {"type": "STRING"}
            },
            "required": ["subject", "object", "which", "action", "time_place", "how", "reason", "consequences", "explain"]
        }

        print(f"Отправка запроса к Deepseek (этап 2 - Context Filtration) с промптом (часть): '{main_message[:50]}...'")
        deepseek_result_2 = initial_filtration(
            prompt=deepseek_prompt_2,
            response_schema=deepseek_response_schema_2
        )

        if isinstance(deepseek_result_2, dict):
            scores_context = [
                deepseek_result_2.get("subject", 0),
                deepseek_result_2.get("object", 0),
                deepseek_result_2.get("which", 0),
                deepseek_result_2.get("action", 0),
                deepseek_result_2.get("time_place", 0),
                deepseek_result_2.get("how", 0),
                deepseek_result_2.get("reason", 0),
                deepseek_result_2.get("consequences", 0)
            ]
            total_score_context = sum(scores_context)
            explain_value_2 = deepseek_result_2.get("explain", "Не удалось получить объяснение (этап 2).")
            
            if total_score_context >= CONTEXT_THRESHOLD:
                filter_value_2 = "Да"
            else:
                filter_value_2 = "Нет"

            print(f"Получен структурированный ответ от Deepseek (этап 2): Сумма баллов={total_score_context}, Фильтр='{filter_value_2}', Объяснение='{str(explain_value_2)[:50]}...'")
        else:
            print(f"Ошибка при получении структурированного ответа от Deepseek (этап 2): {deepseek_result_2}")
            explain_value_2 = str(deepseek_result_2) # Убедимся, что explain_value_2 всегда строка
    # --- Конец второго этапа фильтрации ---

    # --- Третий этап: Оценка эмоциональных и стилистических характеристик (если второй этап вернул "Да") ---
    # Инициализация переменных для оценок и объяснений
    emotion_score, emotion_explain = 0, "N/A"
    image_score, image_explain = 0, "N/A"
    humor_score, humor_explain = 0, "N/A"
    surprise_score, surprise_explain = 0, "N/A"
    drama_score, drama_explain = 0, "N/A"

    # Инициализация экранированных переменных с их дефолтными значениями
    escaped_emotion_score = html.escape(str(emotion_score))
    escaped_emotion_explain = html.escape(emotion_explain)
    escaped_image_score = html.escape(str(image_score))
    escaped_image_explain = html.escape(image_explain)
    escaped_humor_score = html.escape(str(humor_score))
    escaped_humor_explain = html.escape(humor_explain)
    escaped_surprise_score = html.escape(str(surprise_score))
    escaped_surprise_explain = html.escape(surprise_explain)
    escaped_drama_score = html.escape(str(drama_score))
    escaped_drama_explain = html.escape(drama_explain)

    final_filter_value = "Нет"
    total_potential_score = 0
    potential_scores_list = []

    if filter_value_2 == "Да":
        print("Начало третьего этапа фильтрации (оценка характеристик)...")
        evaluation_schema = {
            "type": "OBJECT",
            "properties": {
                "score": {"type": "INTEGER", "minimum": 0, "maximum": 10},
                "explain": {"type": "STRING"}
            },
            "required": ["score", "explain"]
        }

        # Обработка emotion_result
        emotion_result = initial_filtration(
            prompt=f"Текст новости: {main_message}\n\n{EMOTION_INSTRUCTIONS}",
            response_schema=evaluation_schema
        )
        if isinstance(emotion_result, dict):
            emotion_score = emotion_result.get("score", 0)
            emotion_explain = emotion_result.get("explain", "Не получено объяснение.")
        else:
            print(f"Ошибка при оценке эмоциональной яркости: {emotion_result}")
            emotion_explain = str(emotion_result) # Убедимся, что это строка
            emotion_score = 0
        escaped_emotion_score = html.escape(str(emotion_score))
        escaped_emotion_explain = html.escape(emotion_explain)
        print(f"Эмоциональная яркость: {emotion_score}, Объяснение: {str(emotion_explain)[:50]}...")


        # Обработка image_result
        image_result = initial_filtration(
            prompt=f"Текст новости: {main_message}\n\n{IMAGE_INSTRUCTIONS}",
            response_schema=evaluation_schema
        )
        if isinstance(image_result, dict):
            image_score = image_result.get("score", 0)
            image_explain = image_result.get("explain", "Не получено объяснение.")
        else:
            print(f"Ошибка при оценке образности: {image_result}")
            image_explain = str(image_result) # Убедимся, что это строка
            image_score = 0
        escaped_image_score = html.escape(str(image_score))
        escaped_image_explain = html.escape(image_explain)
        print(f"Образность: {image_score}, Объяснение: {str(image_explain)[:50]}...")

        # Обработка humor_result
        humor_result = initial_filtration(
            prompt=f"Текст новости: {main_message}\n\n{HUMOR_INSTRUCTIONS}",
            response_schema=evaluation_schema
        )
        if isinstance(humor_result, dict):
            humor_score = humor_result.get("score", 0)
            humor_explain = humor_result.get("explain", "Не получено объяснение.")
        else:
            print(f"Ошибка при оценке юмора: {humor_result}")
            humor_explain = str(humor_result) # Убедимся, что это строка
            humor_score = 0
        escaped_humor_score = html.escape(str(humor_score))
        escaped_humor_explain = html.escape(humor_explain)
        print(f"Юмор: {humor_score}, Объяснение: {str(humor_explain)[:50]}...")

        # Обработка surprise_result
        surprise_result = initial_filtration(
            prompt=f"Текст новости: {main_message}\n\n{SURPRISE_INSTRUCTIONS}",
            response_schema=evaluation_schema
        )
        if isinstance(surprise_result, dict):
            surprise_score = surprise_result.get("score", 0)
            surprise_explain = surprise_result.get("explain", "Не получено объяснение.")
        else:
            print(f"Ошибка при оценке неожиданности: {surprise_result}")
            surprise_explain = str(surprise_result) # Убедимся, что это строка
            surprise_score = 0
        escaped_surprise_score = html.escape(str(surprise_score))
        escaped_surprise_explain = html.escape(surprise_explain)
        print(f"Неожиданность: {surprise_score}, Объяснение: {str(surprise_explain)[:50]}...")

        # Обработка drama_result
        drama_result = initial_filtration(
            prompt=f"Текст новости: {main_message}\n\n{DRAMA_INSTRUCTIONS}",
            response_schema=evaluation_schema
        )
        if isinstance(drama_result, dict):
            drama_score = drama_result.get("score", 0)
            drama_explain = drama_result.get("explain", "Не получено объяснение.")
        else:
            print(f"Ошибка при оценке драматичности: {drama_result}")
            drama_explain = str(drama_result) # Убедимся, что это строка
            drama_score = 0
        escaped_drama_score = html.escape(str(drama_score))
        escaped_drama_explain = html.escape(drama_explain)
        print(f"Драматичность: {drama_score}, Объяснение: {str(drama_explain)[:50]}...")
        
        potential_scores_list = [emotion_score, image_score, humor_score, surprise_score, drama_score]
        total_potential_score = sum(s for s in potential_scores_list if isinstance(s, int))

        has_max_potential = any(score >= MAX_POTENTIAL for score in potential_scores_list if isinstance(score, int))
        if total_potential_score >= SUM_POTENTIAL and has_max_potential:
            final_filter_value = "Да"
        else:
            final_filter_value = "Нет"
        
        print(f"Финальная фильтрация: Сумма потенциальных баллов={total_potential_score}, Есть MAX_POTENTIAL={has_max_potential}, Результат='{final_filter_value}'")

    else:
        print("Третий этап фильтрации не проводился (второй этап вернул 'Нет').")


    # --- Условная пересылка сообщения в приватную группу (на основе final_filter_value) ---
    if final_filter_value == "Да":
        response_text = (
            f"{main_message}\n\n"
            f"1111\n\n"
            f"{message_link}\n\n"
            f"1111\n\n"
            f"Общий потенциал: {total_potential_score}\n"
            f"1. Эмоции: {emotion_score}\n"
            f"2. Образность: {image_score}\n"
            f"3. Юмор: {humor_score}\n"
            f"4. Неожиданность: {surprise_score}\n"
            f"5. Драма: {drama_score}\n\n"
            f"1111\n\n"
            f"Пока пусто"
        )
        try:
            await context.bot.send_message(chat_id=PRIVATE_GROUP_CHAT_ID, text=response_text)
            print(f"Сообщение успешно отправлено в приватную группу {PRIVATE_GROUP_CHAT_ID} (финальный фильтр: Да).")
            increment_outgoing_messages()
        except Exception as e:
            print(f"Ошибка при отправке сообщения в приватную группу {PRIVATE_GROUP_CHAT_ID}: {e}")
            await update.message.reply_text(f"Произошла ошибка при пересылке сообщения: {e}")
    else:
        print(f"Сообщение НЕ отправлено в приватную группу (финальный фильтр: Нет). Объяснение: {explain_value_2}")
    
    # --- Логирование в отдельный бот (всегда) ---
    if logging_bot and LOGGING_CHAT_ID:
        # Убедимся, что все explain_value_X являются строками перед экранированием
        escaped_main_message = html.escape(main_message)
        escaped_message_link = html.escape(message_link)
        escaped_filter_value_1 = html.escape(filter_value_1)
        escaped_explain_value_1 = html.escape(str(explain_value_1)) # Явное преобразование в str
        escaped_filter_value_2 = html.escape(filter_value_2)
        escaped_total_score_context = html.escape(str(total_score_context))
        escaped_explain_value_2 = html.escape(str(explain_value_2)) # Явное преобразование в str

        # escaped_emotion_score и другие уже обновляются после каждого вызова Deepseek
        # или при ошибке, и там уже происходит str() и html.escape()

        log_message_text = (
            f"<b>Исходное сообщение:</b>\n\n{escaped_main_message}\n\n"
            f"1111\n\n"
            f"Ссылка: {escaped_message_link}\n\n"
            f"1111\n\n"
            f"Фильтр Deepseek (Этап 1): {escaped_filter_value_1}\n"
            f"Context Filtration (Этап 2): {escaped_filter_value_2}\n"
            f"Сумма баллов (Этап 2): {escaped_total_score_context}\n\n"
        )
        
        if filter_value_2 == "Да":
            log_message_text += (
                f"<b>--- Оценки характеристик ---</b>\n"
                f"Эмоциональная яркость: {escaped_emotion_score}\n"
                f"Образность: {escaped_image_score}\n"
                f"Юмор: {escaped_humor_score}\n"
                f"Неожиданность: {escaped_surprise_score}\n"
                f"Драматичность: {escaped_drama_score}\n\n"
                f"Финальный фильтр: {html.escape(final_filter_value)}\n"
                f"Сумма баллов: {html.escape(str(total_potential_score))}\n"
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

