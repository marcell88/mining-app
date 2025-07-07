# services/database_service.py
import sqlite3
import os
from datetime import datetime, timedelta

# Путь к файлу базы данных SQLite
DATABASE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/stats.db')

def initialize_database():
    """
    Инициализирует базу данных SQLite, создавая таблицу 'message_logs', если она не существует.
    Таблица будет хранить логи входящих и исходящих сообщений с временными метками.
    """
    # Создаем директорию 'data', если ее нет
    os.makedirs(os.path.dirname(DATABASE_FILE), exist_ok=True)

    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        # Изменяем схему таблицы для хранения отдельных логов сообщений
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS message_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL, -- 'incoming' или 'outgoing'
                timestamp TEXT NOT NULL -- Формат ISO 8601 (YYYY-MM-DD HH:MM:SS.mmmmmm)
            )
        ''')
        conn.commit()
        print(f"База данных SQLite '{DATABASE_FILE}' успешно инициализирована с таблицей 'message_logs'.")
    except sqlite3.Error as e:
        print(f"Ошибка при инициализации базы данных SQLite: {e}")
    finally:
        if conn:
            conn.close()

def _add_message_log(message_type: str):
    """
    Внутренняя функция для добавления записи о сообщении в базу данных.
    """
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        now = datetime.now().isoformat() # Получаем текущее время в формате ISO 8601
        cursor.execute("INSERT INTO message_logs (type, timestamp) VALUES (?, ?)", (message_type, now))
        conn.commit()
        print(f"Запись о сообщении '{message_type}' добавлена.")
    except sqlite3.Error as e:
        print(f"Ошибка при добавлении записи о сообщении '{message_type}': {e}")
    finally:
        if conn:
            conn.close()

def increment_incoming_messages():
    """
    Добавляет запись о входящем сообщении в базу данных.
    """
    _add_message_log('incoming')

def increment_outgoing_messages():
    """
    Добавляет запись об исходящем сообщении в базу данных.
    """
    _add_message_log('outgoing')

def get_stats() -> dict:
    """
    Получает текущую статистику по входящим и исходящим сообщениям
    (общее количество и за последние 24 часа) из базы данных.
    Возвращает словарь с подробной статистикой.
    """
    conn = None
    stats = {
        'total_incoming': 0,
        'total_outgoing': 0,
        'total_percentage': 0.0,
        'last_24h_incoming': 0,
        'last_24h_outgoing': 0,
        'last_24h_percentage': 0.0
    }
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        # Статистика за все время
        cursor.execute("SELECT type, COUNT(*) FROM message_logs GROUP BY type")
        total_counts = cursor.fetchall()
        for msg_type, count in total_counts:
            if msg_type == 'incoming':
                stats['total_incoming'] = count
            elif msg_type == 'outgoing':
                stats['total_outgoing'] = count
        
        if stats['total_incoming'] > 0:
            stats['total_percentage'] = (stats['total_outgoing'] / stats['total_incoming']) * 100

        # Статистика за последние 24 часа
        # Вычисляем временную метку 24 часа назад
        twenty_four_hours_ago = (datetime.now() - timedelta(hours=24)).isoformat()
        
        cursor.execute(
            "SELECT type, COUNT(*) FROM message_logs WHERE timestamp >= ? GROUP BY type",
            (twenty_four_hours_ago,)
        )
        last_24h_counts = cursor.fetchall()
        for msg_type, count in last_24h_counts:
            if msg_type == 'incoming':
                stats['last_24h_incoming'] = count
            elif msg_type == 'outgoing':
                stats['last_24h_outgoing'] = count
        
        if stats['last_24h_incoming'] > 0:
            stats['last_24h_percentage'] = (stats['last_24h_outgoing'] / stats['last_24h_incoming']) * 100

        return stats

    except sqlite3.Error as e:
        print(f"Ошибка при получении статистики: {e}")
        return stats # Возвращаем дефолтные нули в случае ошибки
    finally:
        if conn:
            conn.close()

def reset_stats():
    """
    Полностью обнуляет все счетчики, удаляя все записи из таблицы message_logs.
    """
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM message_logs") # Удаляем все записи
        conn.commit()
        print("Все счетчики сообщений сброшены до нуля (таблица message_logs очищена).")
    except sqlite3.Error as e:
        print(f"Ошибка при сбросе статистики: {e}")
    finally:
        if conn:
            conn.close()

# Вызываем инициализацию базы данных при загрузке модуля
initialize_database()
