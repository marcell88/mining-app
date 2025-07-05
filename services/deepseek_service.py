# services/deepseek_service.py
import requests
import json
import re
from config.settings import DEEPSEEK_API_KEY

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"

def initial_filtration(
    prompt: str,
    model: str = "deepseek-chat",
    max_tokens: int = 500,
    response_schema: dict = None
) -> dict | str:
    """
    Отправляет запрос к Deepseek Chat API и возвращает сгенерированный текст или структурированный JSON.
    Включает попытку парсинга Markdown-подобного текстового вывода в случае, если модель не возвращает строгий JSON.
    """
    if not DEEPSEEK_API_KEY:
        return "Ошибка: Deepseek API ключ не установлен."

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }

    # Если ожидается структурированный ответ, добавим явную инструкцию в промпт
    modified_prompt = prompt
    if response_schema:
        modified_prompt += "\n\nВерни ответ в формате строгого JSON, соответствующего предоставленной схеме."

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": modified_prompt} # Используем модифицированный промпт
        ],
        "max_tokens": max_tokens,
        "stream": False
    }

    if response_schema:
        payload["generationConfig"] = {
            "responseMimeType": "application/json",
            "responseSchema": response_schema
        }

    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, data=json.dumps(payload))
        response.raise_for_status()

        response_data = response.json()
        
        if response_data and response_data.get("choices"):
            content = response_data["choices"][0]["message"]["content"].strip()
            
            if response_schema:
                # 1. Попытка очистить от markdown-кодовых блоков (```json ... ```)
                content_to_parse = content
                if content.startswith("```json") and content.endswith("```"):
                    content_to_parse = content[len("```json"): -len("```")].strip()
                elif content.startswith("```") and content.endswith("```"):
                    content_to_parse = content[len("```"): -len("```")].strip()

                try:
                    # 2. Попытка декодировать как строгий JSON
                    return json.loads(content_to_parse)
                except json.JSONDecodeError:
                    # 3. Если не строгий JSON, пытаемся парсить как "**key**: value"
                    print(f"Предупреждение: Deepseek вернул нестрогий JSON. Попытка парсинга текстового формата: {content_to_parse[:100]}...")
                    parsed_data = {}
                    
                    lines = content_to_parse.split('\n')
                    pattern = re.compile(r'\*\*(.*?)\*\*:\s*(.*)')

                    for line in lines:
                        match = pattern.search(line.strip())
                        if match:
                            key = match.group(1).strip()
                            value = match.group(2).strip()
                            parsed_data[key] = value
                    
                    # Попытка преобразовать числовые поля в int
                    # Проходимся по всем свойствам в response_schema
                    for prop_name, prop_details in response_schema.get('properties', {}).items():
                        if prop_name in parsed_data and prop_details.get('type') == 'INTEGER':
                            try:
                                parsed_data[prop_name] = int(parsed_data[prop_name])
                            except ValueError:
                                pass # Оставляем как строку, если не число

                    # Убедимся, что все "required" поля из response_schema присутствуют
                    # Если поле отсутствует, добавляем его с дефолтным значением или ошибкой
                    for required_key in response_schema.get('required', []):
                        if required_key not in parsed_data:
                            if response_schema['properties'].get(required_key, {}).get('type') == 'STRING':
                                parsed_data[required_key] = f"Отсутствует '{required_key}' в ответе Deepseek."
                            elif response_schema['properties'].get(required_key, {}).get('type') == 'INTEGER':
                                parsed_data[required_key] = 0 # Дефолтное значение для чисел
                            else:
                                parsed_data[required_key] = "N/A" # Общий дефолт

                    # Финальная проверка: если все required поля присутствуют, возвращаем parsed_data
                    # Иначе, возвращаем ошибку
                    all_required_present = all(key in parsed_data for key in response_schema.get('required', []))
                    
                    if all_required_present:
                        return parsed_data
                    else:
                        return f"Ошибка Deepseek API: Не удалось декодировать JSON или текстовый формат в ожидаемую схему. Отсутствуют обязательные поля. Получено: {content}"
            else:
                return content # Если response_schema не предоставлена, возвращаем сырой текст
        else:
            return f"Ошибка Deepseek API: Неожиданный формат ответа: {response_data}"

    except requests.exceptions.HTTPError as http_err:
        return f"Ошибка HTTP при запросе к Deepseek: {http_err} - {response.text}"
    except requests.exceptions.ConnectionError as conn_err:
        return f"Ошибка подключения к Deepseek: {conn_err}"
    except requests.exceptions.Timeout as timeout_err:
        return f"Таймаут запроса к Deepseek: {timeout_err}"
    except requests.exceptions.RequestException as req_err:
        return f"Общая ошибка запроса к Deepseek: {req_err}"
    except Exception as e:
        return f"Неизвестная ошибка при работе с Deepseek: {e}"

