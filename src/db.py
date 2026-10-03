import sqlite3
from datetime import datetime

# 1. Константная переменная
DB_NAME = "currency_rates.db"

def init_db() -> None:
    """Инициализация БД. Создание таблицы со столбцами: 
    id, имя валюты, курс, дата обновления.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Создаем таблицу, если она еще не существует
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rates (
            id TEXT PRIMARY KEY,
            target_currency TEXT NOT NULL,
            rate REAL NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

def save_rate(id: int, target_currency: str, rate: float) -> None:
    """Сохранение данных о курсе валют в БД.
    Если запись с таким id или валютой уже существует, данные обновляются.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Получаем текущую дату и время для столбца "дата обновления"
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Используем REPLACE (или INSERT OR REPLACE), чтобы обновлять данные при совпадении PRIMARY KEY (id)
    cursor.execute("""
        INSERT INTO rates (id, target_currency, rate, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET 
            rate = excluded.rate,
            updated_at = excluded.updated_at
    """, (id, target_currency, rate, current_date))

    
    conn.commit()
    conn.close()

def get_saved_rate(target_currency: str) -> float:
    """Получение курса по имени валюты из БД."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT rate FROM rates 
        WHERE target_currency = ?
        ORDER BY updated_at DESC 
        LIMIT 1
    ''', (target_currency,))
    
    result = cursor.fetchone()
    conn.close()
    
    # Возвращаем float, если запись найдена, иначе None
    return result[0] if result else None

def get_all_currencies():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT target_currency FROM rates 
        ORDER BY 1
    ''')
    
    result = cursor.fetchall()
    conn.close()
    
    # Возвращаем float, если запись найдена, иначе None
    return [x[0] for x in result] if result else []
