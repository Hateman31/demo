import pytest
import sqlite3
from unittest.mock import patch, MagicMock, mock_open
import tempfile
from datetime import datetime
import os

from db import (
    init_db, 
    save_rate, 
    get_saved_rate, 
    DB_NAME
)

@pytest.fixture
def temp_db(self):
    """Create a temporary database for testing"""
    # Create a temporary file for the database
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()

    # Store the original DB_NAME
    original_db_name = DB_NAME

    # Patch the DB_NAME to use our temporary database
    with patch('db.DB_NAME', temp_file.name):
        # Initialize the database
        init_db()
        yield temp_file.name

    # Cleanup: remove the temporary file
    try:
        os.unlink(temp_file.name)
    except (PermissionError, FileNotFoundError):
        # File might be locked or already deleted, ignore
        pass

@pytest.fixture
def sample_data(self):
    """Sample data for testing"""
    return {
        'id': 1,
        'currency': 'USD',
        'rate': 1.0
    }


class TestInitDb:
    def test_init_db_creates_table(self, clean_db):
        """Проверяет создание таблицы"""
        init_db()
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        # Проверяем существование таблицы
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='rates'")
        result = cursor.fetchone()
        assert result is not None
        conn.close()

class TestSaveRate:
    def test_save_rate_new_record(self, clean_db):
        """Проверяет добавление новой записи"""
        save_rate(1, "USD", 75.50)
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rates WHERE id = ?", (1,))
        row = cursor.fetchone()
        assert row is not None
        assert row[1] == "USD"  # target_currency
        assert row[2] == 75.50  # rate
        conn.close()

    def test_save_rate_update_existing(self, clean_db):
        """Проверяет обновление существующего поля"""
        save_rate(1, "EUR", 80.00)
        save_rate(1, "EUR", 85.00)  # Обновление того же id
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT rate FROM rates WHERE id = ?", (1,))
        row = cursor.fetchone()
        assert row[0] == 85.00
        conn.close()

    def test_save_rate_date_format(self, clean_db):
        """Проверяет формат даты"""
        save_rate(1, "USD", 75.50)
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT updated_at FROM rates")
        date_str = cursor.fetchone()[0]
        
        # Проверяем, что дата соответствует формату YYYY-MM-DD HH:MM:SS
        try:
            datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            pytest.fail("Дата не соответствует ожидаемому формату")
        conn.close()

    def test_save_rate_multiple_currencies(self, clean_db):
        """Проверяет разный набор валют"""
        save_rate(1, "USD", 75.50)
        save_rate(2, "EUR", 80.00)
        save_rate(3, "GBP", 90.00)
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM rates")
        count = cursor.fetchone()[0]
        assert count == 3
        conn.close()

    def test_save_rate_edge_cases(self, clean_db):
        """Проверяет разные диапазоны значений"""
        # Очень маленькое число
        save_rate(1, "USD", 0.00001)
        # Очень большое число
        save_rate(2, "EUR", 999999.99)
        # Отрицательное (если логически допустимо, хотя для курсов редко, но тест на обработку)
        save_rate(3, "GBP", -10.5)
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT rate FROM rates WHERE id = ?", (3,))
        assert cursor.fetchone()[0] == -10.5
        conn.close()

    @patch('db.sqlite3.connect')
    def test_save_rate_database_connection_error(self, mock_connect, clean_db):
        """Проверяет разрыв соединения с БД"""
        mock_connect.side_effect = sqlite3.Error("Database connection failed")
        
        with pytest.raises(sqlite3.Error):
            save_rate(1, "USD", 75.50)

    @patch('db.sqlite3.connect')
    def test_save_rate_commit_error(self, mock_connect, clean_db):
        """Проверяет ошибку при коммите данных в БД"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.commit.side_effect = sqlite3.Error("Commit failed")
        
        with pytest.raises(sqlite3.Error):
            save_rate(1, "USD", 75.50)

    def test_save_rate_parameter_types(self, clean_db):
        """Проверяет разные типы данных параметров"""
        # Целочисленный id
        save_rate(1, "USD", 75.50)
        # Строковый id (если бы логика позволяла, но здесь id int)
        # rate может быть float
        save_rate(2, "RUB", 10.5)
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rates")
        rows = cursor.fetchall()
        assert len(rows) == 2
        conn.close()

    def test_save_rate_sql_injection_protection(self, clean_db):
        """Проверяет защиту на SQL-инъекции"""
        # Пытаемся передать SQL-инъекцию через target_currency
        malicious_currency = "'; DROP TABLE rates; --"
        save_rate(1, malicious_currency, 75.50)
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        # Проверяем, что таблица все еще существует
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='rates'")
        result = cursor.fetchone()
        assert result is not None
        conn.close()

class TestGetSavedRate:
    def test_get_saved_rate_success(self, clean_db):
        """Проверяет успешность получения данных из БД"""
        save_rate(1, "USD", 75.50)
        rate = get_saved_rate("USD")
        assert rate == 75.50

    def test_get_saved_rate_default_currency(self, clean_db):
        """Проверяет получение курса стандартной валюты"""
        save_rate(1, "USD", 75.50)
        # Стандартная валюта (предположим USD)
        rate = get_saved_rate("USD")
        assert rate is not None

    def test_get_saved_rate_nonexistent_currency(self, clean_db):
        """Проверяет получение несуществующей валюты"""
        save_rate(1, "USD", 75.50)
        rate = get_saved_rate("BTC")
        assert rate is None

    def test_get_saved_rate_empty_database(self, clean_db):
        """Проверяет получение данных из пустой БД"""
        # Инициализируем БД, но ничего не сохраняем
        init_db()
        rate = get_saved_rate("USD")
        assert rate is None

    def test_get_saved_rate_multiple_currencies(self, clean_db):
        """Проверяет получение множества валют"""
        save_rate(1, "USD", 75.50)
        save_rate(2, "EUR", 80.00)
        
        usd_rate = get_saved_rate("USD")
        eur_rate = get_saved_rate("EUR")
        
        assert usd_rate == 75.50
        assert eur_rate == 80.00

    def test_get_saved_rate_case_sensitivity(self, clean_db):
        """Проверяет чувствительность написания параметров"""
        save_rate(1, "USD", 75.50)
        
        # Верхний регистр
        rate_upper = get_saved_rate("USD")
        # Нижний регистр
        rate_lower = get_saved_rate("usd")
        
        assert rate_upper == 75.50
        assert rate_lower is None  # База данных чувствительна к регистру

    def test_get_saved_rate_sql_injection_protection(self, clean_db):
        """Проверяет защиту на SQL-инъекции"""
        save_rate(1, "USD", 75.50)
        
        malicious_currency = "'; DROP TABLE rates; --"
        # Функция должна вернуть None или корректное значение, а не выбросить ошибку
        rate = get_saved_rate(malicious_currency)
        assert rate is None  # Таблица должна остаться целой
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='rates'")
        assert cursor.fetchone() is not None
        conn.close()

    @patch('db.sqlite3.connect')
    def test_get_saved_rate_database_connection_error(self, mock_connect, clean_db):
        """Проверяет разрыв соединения с БД"""
        mock_connect.side_effect = sqlite3.Error("Database connection failed")
        
        with pytest.raises(sqlite3.Error):
            get_saved_rate("USD")
            