# handlers/message_handler.py
from telegram import Update, Bot
from telegram.ext import ContextTypes
from config.settings import PRIVATE_GROUP_CHAT_ID, CONTEXT_THRESHOLD, MAX_POTENTIAL, SUM_POTENTIAL
from services.database_service import increment_incoming_messages, increment_outgoing_messages
from services.telegram_logger import send_log_message
from services.deepseek_processor import (
    perform_initial_filtration,
    perform_context_filtration,
    evaluate_characteristics,
    generate_commentary_recommendations
)
import html


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

    # --- Первый этап фильтрации ---
    filter_value_1, explain_value_1 = await perform_initial_filtration(main_message, message_link)
    # --- Конец первого этапа фильтрации ---

    # Если первый фильтр вернул "Нет", прекращаем дальнейшую обработку
    if filter_value_1 == "Нет":
        print(f"Сообщение НЕ прошло первичную фильтрацию. Причина: {explain_value_1}")
        # Логируем результат первого этапа и завершаем функцию
        await send_log_message(
            main_message=main_message,
            message_link=message_link,
            filter_value_1=filter_value_1,
            explain_value_1=explain_value_1,
            filter_value_2="Не проводился", # Указываем, что второй этап не проводился
            total_score_context=0,
            explain_value_2="Не проводился", # Указываем, что второй этап не проводился
            final_filter_value="Нет", # Финальный фильтр тоже "Нет"
            total_potential_score=0,
            emotion_score=0,
            emotion_explain="Не проводился",
            image_score=0,
            image_explain="Не проводился",
            humor_score=0,
            humor_explain="Не проводился",
            surprise_score=0,
            surprise_explain="Не проводился",
            drama_score=0,
            drama_explain="Не проводился",
            is_filtered_by_stage_2=False # Флаг, что 3-й этап не проводился
        )
        return # Завершаем выполнение функции

    # --- Второй этап фильтрации (Context Filtration) ---
    filter_value_2, total_score_context, explain_value_2, is_filtered_by_stage_2 = await perform_context_filtration(main_message)
    # --- Конец второго этапа фильтрации ---

    # Если второй фильтр вернул "Нет", прекращаем дальнейшую обработку
    if filter_value_2 == "Нет":
        print(f"Сообщение НЕ прошло контекстную фильтрацию. Причина: {explain_value_2}")
        # Логируем результат второго этапа и завершаем функцию
        await send_log_message(
            main_message=main_message,
            message_link=message_link,
            filter_value_1=filter_value_1, # Первый фильтр был "Да"
            explain_value_1=explain_value_1, # Объяснение первого фильтра
            filter_value_2=filter_value_2, # Второй фильтр был "Нет"
            total_score_context=total_score_context, # Фактический балл второго этапа
            explain_value_2=explain_value_2, # Объяснение второго фильтра
            final_filter_value="Нет", # Финальный фильтр тоже "Нет"
            total_potential_score=0,
            emotion_score=0,
            emotion_explain="Не проводился",
            image_score=0,
            image_explain="Не проводился",
            humor_score=0,
            humor_explain="Не проводился",
            surprise_score=0,
            surprise_explain="Не проводился",
            drama_score=0,
            drama_explain="Не проводился",
            is_filtered_by_stage_2=False # Флаг, что 3-й этап не проводился
        )
        return # Завершаем выполнение функции

    # --- Третий этап: Оценка эмоциональных и стилистических характеристик ---
    emotion_score, emotion_explain = 0, "N/A"
    image_score, image_explain = 0, "N/A"
    humor_score, humor_explain = 0, "N/A"
    surprise_score, surprise_explain = 0, "N/A"
    drama_score, drama_explain = 0, "N/A"

    final_filter_value = "Нет"
    total_potential_score = 0
    potential_scores_list = []
    commentary_recommendations = "Рекомендации пока отсутствуют."

    if filter_value_2 == "Да": # Этот блок выполняется, только если второй фильтр был "Да"
        print("Начало третьего этапа фильтрации (оценка характеристик)...")
        (
            emotion_score, emotion_explain,
            image_score, image_explain,
            humor_score, humor_explain,
            surprise_score, surprise_explain,
            drama_score, drama_explain,
            total_potential_score, potential_scores_list
        ) = await evaluate_characteristics(main_message)

        has_max_potential = any(score >= MAX_POTENTIAL for score in potential_scores_list if isinstance(score, int))
        if total_potential_score >= SUM_POTENTIAL and has_max_potential:
            final_filter_value = "Да"
            commentary_recommendations = await generate_commentary_recommendations(
                main_message,
                emotion_score, emotion_explain, # Передаем все оценки и объяснения
                image_score, image_explain,
                humor_score, humor_explain,
                surprise_score, surprise_explain,
                drama_score, drama_explain
            )
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
            f"Рекомендации: {commentary_recommendations}"
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
    await send_log_message(
        main_message=main_message,
        message_link=message_link,
        filter_value_1=filter_value_1,
        explain_value_1=explain_value_1,
        filter_value_2=filter_value_2,
        total_score_context=total_score_context,
        explain_value_2=explain_value_2,
        final_filter_value=final_filter_value,
        total_potential_score=total_potential_score,
        emotion_score=emotion_score,
        emotion_explain=emotion_explain,
        image_score=image_score,
        image_explain=image_explain,
        humor_score=humor_score,
        humor_explain=humor_explain,
        surprise_score=surprise_score,
        surprise_explain=surprise_explain, # Исправлена опечатка
        drama_score=drama_score,
        drama_explain=drama_explain,
        is_filtered_by_stage_2=is_filtered_by_stage_2
    )

