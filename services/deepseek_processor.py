# services/deepseek_processor.py
from services.deepseek_service import deepseek_request
import prompts # Изменено: импортируем модуль prompts целиком
from datetime import datetime

async def perform_initial_filtration(main_message: str, message_link: str) -> tuple[str, str]:
    """
    Выполняет первый этап фильтрации сообщения с помощью Deepseek.
    Возвращает кортеж (filter_value_1, explain_value_1).
    """
    deepseek_prompt_1 = f"Сообщение: {main_message}\nСсылка: {message_link}\n\n{prompts.FILTER_INSTRUCTIONS}" # Изменено
    
    deepseek_response_schema_1 = {
        "type": "OBJECT",
        "properties": {
            "filter": {"type": "STRING", "enum": ["Да", "Нет"]},
            "explain": {"type": "STRING"}
        },
        "required": ["filter", "explain"]
    }

    print(f"Отправка запроса к Deepseek (этап 1) с промптом (часть): '{main_message[:50]}...'")
    deepseek_result_1 = deepseek_request(
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
        explain_value_1 = str(deepseek_result_1)
    
    return filter_value_1, explain_value_1

async def perform_context_filtration(main_message: str) -> tuple[str, int, str, bool]:
    """
    Выполняет второй этап фильтрации сообщения (Context Filtration) с помощью Deepseek.
    Возвращает кортеж (filter_value_2, total_score_context, explain_value_2, is_filtered_by_stage_2).
    """
    filter_value_2 = "Нет"
    total_score_context = 0
    explain_value_2 = "Второй этап фильтрации не проводился (первый этап вернул 'Нет')."
    is_filtered_by_stage_2 = False # Флаг для лог-бота, чтобы знать, проводился ли 3-й этап

    current_date = datetime.now().strftime("%Y-%m-%d")
    deepseek_prompt_2 = f"Текущая дата: {current_date}\nСообщение: {main_message}\n\n{prompts.CONTEXT_FILTRATION_INSTRUCTIONS}" # Изменено

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
    deepseek_result_2 = deepseek_request(
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
        
        # Импортируем CONTEXT_THRESHOLD из settings, чтобы использовать его здесь
        from config.settings import CONTEXT_THRESHOLD
        if total_score_context >= CONTEXT_THRESHOLD:
            filter_value_2 = "Да"
            is_filtered_by_stage_2 = True
        else:
            filter_value_2 = "Нет"

        print(f"Получен структурированный ответ от Deepseek (этап 2): Сумма баллов={total_score_context}, Фильтр='{filter_value_2}', Объяснение='{str(explain_value_2)[:50]}...'")
    else:
        print(f"Ошибка при получении структурированного ответа от Deepseek (этап 2): {deepseek_result_2}")
        explain_value_2 = str(deepseek_result_2)
    
    return filter_value_2, total_score_context, explain_value_2, is_filtered_by_stage_2

async def evaluate_characteristics(main_message: str) -> tuple[int, str, int, str, int, str, int, str, int, str, int, list]:
    """
    Выполняет третий этап фильтрации: оценку эмоциональных и стилистических характеристик.
    Возвращает все оценки и объяснения, а также общий потенциал и список баллов.
    """
    emotion_score, emotion_explain = 0, "N/A"
    image_score, image_explain = 0, "N/A"
    humor_score, humor_explain = 0, "N/A"
    surprise_score, surprise_explain = 0, "N/A"
    drama_score, drama_explain = 0, "N/A"

    evaluation_schema = {
        "type": "OBJECT",
        "properties": {
            "score": {"type": "INTEGER", "minimum": 0, "maximum": 10},
            "explain": {"type": "STRING"}
        },
        "required": ["score", "explain"]
    }

    # Обработка emotion_result
    emotion_result = deepseek_request(
        prompt=f"Текст новости: {main_message}\n\n{prompts.EMOTION_INSTRUCTIONS}", # Изменено
        response_schema=evaluation_schema
    )
    if isinstance(emotion_result, dict):
        emotion_score = emotion_result.get("score", 0)
        emotion_explain = emotion_result.get("explain", "Не получено объяснение.")
    else:
        print(f"Ошибка при оценке эмоциональной яркости: {emotion_result}")
        emotion_explain = str(emotion_result)
        emotion_score = 0
    print(f"Эмоциональная яркость: {emotion_score}, Объяснение: {str(emotion_explain)[:50]}...")


    # Обработка image_result
    image_result = deepseek_request(
        prompt=f"Текст новости: {main_message}\n\n{prompts.IMAGE_INSTRUCTIONS}", # Изменено
        response_schema=evaluation_schema
    )
    if isinstance(image_result, dict):
        image_score = image_result.get("score", 0)
        image_explain = image_result.get("explain", "Не получено объяснение.")
    else:
        print(f"Ошибка при оценке образности: {image_result}")
        image_explain = str(image_result)
        image_score = 0
    print(f"Образность: {image_score}, Объяснение: {str(image_explain)[:50]}...")

    # Обработка humor_result
    humor_result = deepseek_request(
        prompt=f"Текст новости: {main_message}\n\n{prompts.HUMOR_INSTRUCTIONS}", # Изменено
        response_schema=evaluation_schema
    )
    if isinstance(humor_result, dict):
        humor_score = humor_result.get("score", 0)
        humor_explain = humor_result.get("explain", "Не получено объяснение.")
    else:
        print(f"Ошибка при оценке юмора: {humor_result}")
        humor_explain = str(humor_result)
        humor_score = 0
    print(f"Юмор: {humor_score}, Объяснение: {str(humor_explain)[:50]}...")

    # Обработка surprise_result
    surprise_result = deepseek_request(
        prompt=f"Текст новости: {main_message}\n\n{prompts.SURPRISE_INSTRUCTIONS}", # Изменено
        response_schema=evaluation_schema
    )
    if isinstance(surprise_result, dict):
        surprise_score = surprise_result.get("score", 0)
        surprise_explain = surprise_result.get("explain", "Не получено объяснение.")
    else:
        print(f"Ошибка при оценке неожиданности: {surprise_result}")
        surprise_explain = str(surprise_result)
        surprise_score = 0
    print(f"Неожиданность: {surprise_score}, Объяснение: {str(surprise_explain)[:50]}...")

    # Обработка drama_result
    drama_result = deepseek_request(
        prompt=f"Текст новости: {main_message}\n\n{prompts.DRAMA_INSTRUCTIONS}", # Изменено
        response_schema=evaluation_schema
    )
    if isinstance(drama_result, dict):
        drama_score = drama_result.get("score", 0)
        drama_explain = drama_result.get("explain", "Не получено объяснение.")
    else:
        print(f"Ошибка при оценке драматичности: {drama_result}")
        drama_explain = str(drama_result)
        drama_score = 0
    print(f"Драматичность: {drama_score}, Объяснение: {str(drama_explain)[:50]}...")
    
    potential_scores_list = [emotion_score, image_score, humor_score, surprise_score, drama_score]
    total_potential_score = sum(s for s in potential_scores_list if isinstance(s, int))

    return (
        emotion_score, emotion_explain,
        image_score, image_explain,
        humor_score, humor_explain,
        surprise_score, surprise_explain,
        drama_score, drama_explain,
        total_potential_score, potential_scores_list
    )

async def generate_commentary_recommendations(
    main_message: str,
    emotion_explain: str,
    image_explain: str,
    humor_explain: str,
    surprise_explain: str,
    drama_explain: str
) -> str:
    """
    Генерирует рекомендации по написанию художественного комментария к новости
    на основе объяснений Deepseek по различным характеристикам.
    """
    combined_explains = (
        f"Эмоциональная яркость: {emotion_explain}\n"
        f"Образность: {image_explain}\n"
        f"Юмор: {humor_explain}\n"
        f"Неожиданность: {surprise_explain}\n"
        f"Драматичность: {drama_explain}\n"
    )

    commentary_prompt = (
        f"На основе следующей новости и анализа ее характеристик, напиши рекомендации "
        f"для создания художественного комментария. Сфокусируйся на том, что в новости "
        f"рождает особенно большой интерес для читателя, делая упор на эмоциональную яркость, "
        f"образность, юмор, неожиданность и драматичность. Избегай прямого цитирования новости, "
        f"перефразируй и интерпретируй.\n\n"
        f"Новость: {main_message}\n\n"
        f"Анализ характеристик:\n{combined_explains}\n\n"
        f"Рекомендации:"
    )

    print(f"Отправка запроса к Deepseek для генерации рекомендаций: '{commentary_prompt[:100]}...'")
    recommendations_result = deepseek_request(
        prompt=commentary_prompt,
        max_tokens=300 # Ограничим длину рекомендаций
    )

    if isinstance(recommendations_result, str):
        return recommendations_result
    else:
        # Если Deepseek вернул словарь, но мы ожидали строку, или произошла другая ошибка
        print(f"Ошибка при получении рекомендаций от Deepseek: {recommendations_result}")
        return "Не удалось сгенерировать рекомендации."

