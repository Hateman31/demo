import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Добавляем путь к src для импорта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main import CurrencyConverterApp
import db as db_handler
import api

class TestCurrencyConverterApp(unittest.TestCase):
    
    def setUp(self):
        """Создаёт тестовое окружение перед каждым тестом."""
        self.app = CurrencyConverterApp.__new__(CurrencyConverterApp)
        self.app.root = MagicMock()
        self.app.log_text = MagicMock()
        self.app.currencies = None
        self.app.loan_var = MagicMock()
        self.app.loan_time_var = MagicMock()
        self.app.annual_interest_var = MagicMock()
        self.app.amount_to_convert_var = MagicMock()
        self.app.target_var = MagicMock()
        self.app.target_entry = MagicMock()
        self.app.monthly_label = MagicMock()
        self.app.loan_sum_label = MagicMock()
        self.app.interest_label = MagicMock()
        self.app.result_label = MagicMock()
        
        # Сброс логов
        self.app.log_text.config.reset_mock()
        self.app.log_text.insert.reset_mock()
        self.app.log_text.see.reset_mock()

    def log(self, message: str) -> None:
        """Вспомогательный метод для имитации логгера"""
        self.app.log_text.config.reset_mock()
        self.app.log_text.insert.reset_mock()
        self.app.log_text.see.reset_mock()
        # Имитация работы log
        pass

    @patch.object(db_handler, 'get_saved_rate')
    def test_calculate_loan_success(self, mock_get_saved_rate):
        """Проверяет правильность вычисления кредита"""
        # Установка значений переменных
        self.app.loan_var.get.return_value = "100000"
        self.app.loan_time_var.get.return_value = "12"
        self.app.annual_interest_var.get.return_value = "12.0"
        
        # Вызов метода
        self.app.calculate_loan()
        
        # Проверка результатов
        # Ежемесячный платёж: 100000 * (0.01 * (1.01**12)) / ((1.01**12) - 1)
        # monthly_rate = 0.01
        # monthly_payment = 100000 * (0.01 * 1.126825) / (1.126825 - 1)
        # = 100000 * 0.01126825 / 0.126825 = 8884.87
        expected_monthly = 8884.87
        self.app.monthly_label.config.assert_called()
        call_args = self.app.monthly_label.config.call_args
        self.assertIn("Ежемесячный платёж:", call_args[0][0])
        self.assertGreater(float(call_args[0][0].split(": ")[1]), expected_monthly - 0.1)
        self.assertLess(float(call_args[0][0].split(": ")[1]), expected_monthly + 0.1)

    @patch.object(db_handler, 'get_saved_rate')
    def test_calculate_loan_invalid_loan_amount(self, mock_get_saved_rate):
        """Проверяет на наличие ошибок, если введена неправильная сумма кредита"""
        # Установка неверных значений
        self.app.loan_var.get.return_value = "-1000"
        self.app.loan_time_var.get.return_value = "12"
        self.app.annual_interest_var.get.return_value = "12.0"
        
        # Вызов метода
        self.app.calculate_loan()
        
        # Проверка, что логирование ошибки произошло
        self.app.log_text.insert.assert_called()
        log_text = self.app.log_text.insert.call_args[0][0]
        self.assertIn("Ошибка", log_text)
        self.assertIn("Сумма", log_text)

    @patch.object(db_handler, 'get_saved_rate')
    def test_convert_success(self, mock_get_saved_rate):
        """Проверяет успешность конвертации"""
        # Установка значений
        self.app.target_var.get.return_value = "USD"
        self.app.amount_to_convert_var.get.return_value = "1000"
        mock_get_saved_rate.return_value = 75.5
        
        # Вызов метода
        self.app.convert()
        
        # Проверка результата
        self.app.result_label.config.assert_called()
        call_args = self.app.result_label.config.call_args
        self.assertIn("Результат:", call_args[0][0])
        # 1000 / 75.5 = 13.245...
        self.assertIn("13.25", call_args[0][0])  # округление до 2 знаков

    @patch.object(db_handler, 'get_saved_rate')
    def test_convert_none_rate(self, mock_get_saved_rate):
        """Проверяет конвертацию, когда курс является None"""
        # Установка значений
        self.app.target_var.get.return_value = "EUR"
        self.app.amount_to_convert_var.get.return_value = "1000"
        mock_get_saved_rate.return_value = None
        
        # Вызов метода
        self.app.convert()
        
        # Проверка, что выведена ошибка
        self.app.result_label.config.assert_called()
        call_args = self.app.result_label.config.call_args
        self.assertIn("курс не найден", call_args[0][0])

    @patch.object(db_handler, 'get_saved_rate')
    def test_convert_exception(self, mock_get_saved_rate):
        """Проверяет обработку исключений"""
        # Установка значений, вызывающих исключение
        self.app.target_var.get.return_value = "USD"
        self.app.amount_to_convert_var.get.return_value = "not_a_number"
        
        # Вызов метода
        self.app.convert()
        
        # Проверка, что логирование ошибки произошло
        self.app.log_text.insert.assert_called()
        log_text = self.app.log_text.insert.call_args[0][0]
        self.assertIn("Ошибка", log_text)
        self.assertIn("Некорректная сумма", log_text)

    @patch('api.fetch_rates')
    @patch.object(db_handler, 'save_rate')
    def test_update_db_success(self, mock_save_rate, mock_fetch_rates):
        """Проверяет успешность обновления БД"""
        # Mock данных от API
        mock_fetch_rates.return_value = {
            'Valute': {
                'USD': {'Nominal': 1, 'Value': 75.5},
                'EUR': {'Nominal': 1, 'Value': 85.0}
            }
        }
        
        # Вызов метода
        self.app.update_db()
        
        # Проверка, что save_rate был вызван
        self.assertTrue(mock_save_rate.called)
        self.app.log_text.insert.assert_called()
        log_text = self.app.log_text.insert.call_args[0][0]
        self.assertIn("База данных обновлена", log_text)

    @patch('api.fetch_rates')
    @patch.object(db_handler, 'save_rate')
    def test_update_db_empty_rates(self, mock_save_rate, mock_fetch_rates):
        """Проверяет обновление БД пустым списком курсов"""
        # Mock пустых данных от API
        mock_fetch_rates.return_value = {'Valute': {}}
        
        # Вызов метода
        self.app.update_db()
        
        # Проверка, что save_rate не был вызван или вызван 0 раз
        self.assertFalse(mock_save_rate.called)
        self.app.log_text.insert.assert_called()
        log_text = self.app.log_text.insert.call_args[0][0]
        self.assertIn("База данных обновлена", log_text)

if __name__ == '__main__':
    unittest.main()