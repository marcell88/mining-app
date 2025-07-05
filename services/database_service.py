# services/database_service.py
import sqlite3
import os

# Путь к файлу базы данных SQLite
DATABASE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/stats.db')

def initialize_database():
    """
    Инициализирует базу данных SQLite, создавая таблицу 'stats', если она не существует.
    Таблица будет хранить счетчики входящих и исходящих сообщений.
    """
    # Создаем директорию 'data', если ее нет
    os.makedirs(os.path.dirname(DATABASE_FILE), exist_ok=True)

    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stats (
                id INTEGER PRIMARY KEY,
                incoming_messages INTEGER DEFAULT 0,
                outgoing_messages INTEGER DEFAULT 0
            )
        ''')
        # Проверяем, есть ли уже запись, если нет - создаем
        cursor.execute("SELECT COUNT(*) FROM stats")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO stats (id, incoming_messages, outgoing_messages) VALUES (1, 0, 0)")
        conn.commit()
        print(f"База данных SQLite '{DATABASE_FILE}' успешно инициализирована.")
    except sqlite3.Error as e:
        print(f"Ошибка при инициализации базы данных SQLite: {e}")
    finally:
        if conn:
            conn.close()

def increment_incoming_messages():
    """
    Инкрементирует счетчик входящих сообщений в базе данных.
    """
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("UPDATE stats SET incoming_messages = incoming_messages + 1 WHERE id = 1")
        conn.commit()
        print("Счетчик входящих сообщений инкрементирован.")
    except sqlite3.Error as e:
        print(f"Ошибка при инкрементировании входящих сообщений: {e}")
    finally:
        if conn:
            conn.close()

def increment_outgoing_messages():
    """
    Инкрементирует счетчик исходящих сообщений в базе данных.
    """
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("UPDATE stats SET outgoing_messages = outgoing_messages + 1 WHERE id = 1")
        conn.commit()
        print("Счетчик исходящих сообщений инкрементирован.")
    except sqlite3.Error as e:
        print(f"Ошибка при инкрементировании исходящих сообщений: {e}")
    finally:
        if conn:
            conn.close()

def get_stats():
    """
    Получает текущее количество входящих и исходящих сообщений из базы данных.
    Возвращает кортеж (incoming_messages, outgoing_messages).
    """
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT incoming_messages, outgoing_messages FROM stats WHERE id = 1")
        result = cursor.fetchone()
        if result:
            return result
        return (0, 0) # Возвращаем нули, если запись не найдена (хотя initialize_database должна ее создать)
    except sqlite3.Error as e:
        print(f"Ошибка при получении статистики: {e}")
        return (0, 0)
    finally:
        if conn:
            conn.close()

def reset_stats():
    """
    Обнуляет счетчики входящих и исходящих сообщений в базе данных.
    """
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("UPDATE stats SET incoming_messages = 0, outgoing_messages = 0 WHERE id = 1")
        conn.commit()
        print("Счетчики входящих и исходящих сообщений сброшены до нуля.")
    except sqlite3.Error as e:
        print(f"Ошибка при сбросе статистики: {e}")
    finally:
        if conn:
            conn.close()

# Вызываем инициализацию базы данных при загрузке модуля
initialize_database()
