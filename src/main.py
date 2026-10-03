import tkinter as tk
from tkinter import ttk
import db as db_handler
import api
from pprint import pprint

class CurrencyConverterApp:
    def __init__(self):
        # Инициализация окна приложения
        self.root = tk.Tk()
        self.root.title("Валютный конвертер и Кредитный калькулятор")
        self.root.geometry("600x750")
        self.currencies = None
        
        # Шаг 3 ТЗ: Инициализация БД
        db_handler.init_db()

        self.set_currencies()

        # pprint(
        #     db_handler.get_all_currencies()
        # )
        # raise SystemExit
        
        # Шаг 3 ТЗ: Создание виджетов
        self.create_widgets()
        
        # Заполнение выпадающего списка валют при старте
        self.refresh_combobox_values()
        self.log("Приложение готово к работе.")


    def set_currencies(self):
        rates_json = api.fetch_rates()
        currencies = {}

        if rates_json:
            currencies = rates_json.get('Valute',currencies)

        for currency in currencies:
            rate_value = currencies[currency]['Value']
            id_ = currencies[currency]['ID']

            db_handler.save_rate(
                id=id_
                ,target_currency=currency
                ,rate=rate_value
            )

    def create_widgets__obsolete(self):
        print("create_widgets started")

        label = tk.Label(self.root, text="HELLO")
        label.pack()

        print("create_widgets finished")


    def create_widgets(self):
        """Создаёт UI-компоненты для навигации в приложении."""
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ==========================================
        # РАЗДЕЛ: ЛОГГЕР
        # ==========================================
        log_frame = ttk.LabelFrame(main_frame, text=" Логгер ", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = tk.Text(log_frame, height=6, state=tk.DISABLED, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # return
        
        # ==========================================
        # РАЗДЕЛ: КРЕДИТНЫЙ КАЛЬКУЛЯТОР (ТЗ Шаг 4)
        # ==========================================
        loan_frame = ttk.LabelFrame(main_frame, text=" Кредитный калькулятор ", padding="10")
        loan_frame.pack(fill=tk.X, pady=5)

        # return
        # Поле ввода: Сумма кредита
        self.loan_var = tk.StringVar()
        ttk.Label(loan_frame, text="Сумма кредита:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(loan_frame, textvariable=self.loan_var, width=25).grid(row=0, column=1, pady=2, padx=5)
        
        # Поле ввода: Срок кредита
        self.loan_time_var = tk.StringVar()
        ttk.Label(loan_frame, text="Срок (в месяцах):").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Entry(loan_frame, textvariable=self.loan_time_var, width=25).grid(row=1, column=1, pady=2, padx=5)
        
        # Поле ввода: Процентная ставка
        self.annual_interest_var = tk.StringVar()
        ttk.Label(loan_frame, text="Процентная ставка (%):").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Entry(loan_frame, textvariable=self.annual_interest_var, width=25).grid(row=2, column=1, pady=2, padx=5)
        
        # Кнопка расчёта
        ttk.Button(loan_frame, text="Рассчитать кредит", command=self.calculate_loan).grid(row=3, column=0, columnspan=2, pady=10)
        
        # Метки вывода результатов
        self.monthly_label = ttk.Label(loan_frame, text="Ежемесячный платёж: —")
        self.monthly_label.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        self.loan_sum_label = ttk.Label(loan_frame, text="Сумма всех платежей: —")
        self.loan_sum_label.grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        self.interest_label = ttk.Label(loan_frame, text="Начисленные проценты: —")
        self.interest_label.grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        # ==========================================
        # РАЗДЕЛ: КОНВЕРТЕР ВАЛЮТ (ТЗ Шаг 4)
        # ==========================================
        conv_frame = ttk.LabelFrame(main_frame, text=" Конвертер валют ", padding="10")
        conv_frame.pack(fill=tk.X, pady=10)
        
        # Поле ввода суммы для конвертации (добавлено для удобства использования)
        ttk.Label(conv_frame, text="Сумма для конвертации (RUB):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.amount_to_convert_var = tk.StringVar(value="1000")
        ttk.Entry(conv_frame, textvariable=self.amount_to_convert_var, width=25).grid(row=0, column=1, pady=5, padx=5)
        
        # Начальная валюта
        self.base_var = tk.StringVar(value="RUB")
        ttk.Label(conv_frame, text="Начальная валюта:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Label(conv_frame, textvariable=self.base_var, font=('Arial', 10, 'bold')).grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Выбор искомой валюты
        self.target_var = tk.StringVar()
        ttk.Label(conv_frame, text="Выбор искомой валюты:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.target_entry = ttk.Combobox(conv_frame, textvariable=self.target_var, state="readonly", width=22)
        self.target_entry.grid(row=2, column=1, pady=5, padx=5)
        
        # Кнопка конвертации
        ttk.Button(conv_frame, text="Конвертировать", command=self.convert).grid(row=3, column=0, columnspan=2, pady=10)
        
        # Вывод результата
        self.result_label = ttk.Label(conv_frame, text="Результат: —", font=('Arial', 10, 'bold'))
        self.result_label.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Кнопка обновления курса валют
        ttk.Button(conv_frame, text="Обновить курс валют", command=self.update_db).grid(row=5, column=0, columnspan=2, pady=5)

    def log(self, message: str) -> None:
        """Выводит лог действий в специальную панель."""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f">> {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def is_loan_invalid(self, value: float, message: str) -> bool:
        """Проверяет, что значения кредитного калькулятора больше 0."""
        if value <= 0:
            self.log(f"Ошибка: {message} должно быть больше 0.")
            return True
        return False

    def calculate_loan(self) -> None:
        """Рассчитывает ежемесячный платёж, сумму всех платежей и начисленные проценты."""
        try:
            amount = float(self.loan_var.get())
            months = float(self.loan_time_var.get())
            annual_rate = float(self.annual_interest_var.get())
            
            if (self.is_loan_invalid(amount, "Сумма") or 
                self.is_loan_invalid(months, "Количество месяцев") or 
                self.is_loan_invalid(annual_rate, "Процентная ставка")):
                return
            
            monthly_rate = (annual_rate / 100) / 12
            if monthly_rate > 0:
                monthly_payment = amount * (monthly_rate * (1 + monthly_rate) ** months) / (((1 + monthly_rate) ** months) - 1)
            else:
                monthly_payment = amount / months
                
            total_payment = monthly_payment * months
            overpayment = total_payment - amount
            
            self.monthly_label.config(text=f"Ежемесячный платёж: {monthly_payment:.2f}")
            self.loan_sum_label.config(text=f"Сумма всех платежей: {total_payment:.2f}")
            self.interest_label.config(text=f"Начисленные проценты: {overpayment:.2f}")
            
            self.log(f"Расчёт кредита: {amount} на {int(months)} мес. под {annual_rate}%")
        except ValueError:
            self.log("Ошибка: Проверьте правильность ввода чисел в калькуляторе.")

    def convert(self) -> None:
        """Конвертирует RUB в выбранную валюту."""
        target_curr = self.target_var.get()
        if not target_curr:
            self.log("Ошибка: Выберите валюту из списка.")
            return
            
        try:
            amount_rub = float(self.amount_to_convert_var.get())
            if amount_rub <= 0:
                self.log("Ошибка: Сумма для конвертации должна быть больше 0.")
                return
        except ValueError:
            self.log("Ошибка: Некорректная сумма для конвертации.")
            return
            
        rate = db_handler.get_saved_rate(target_curr)
        if rate:
            converted_value = amount_rub / rate
            self.result_label.config(text=f"Результат: {amount_rub} RUB = {converted_value:.2f} {target_curr}")
            self.log(f"Конвертация: {amount_rub} RUB -> {target_curr} по курсу {rate:.4f}")
        else:
            self.result_label.config(text="Результат: курс не найден в БД")
            self.log(f"Ошибка: Курс для {target_curr} отсутствует. Сначала обновите БД.")

    def update_db(self) -> None:
        """Обновляет БД на актуальные данные."""
        self.log("Запрос актуальных курсов валют из API...")
        data = api.fetch_rates()
        
        if not data or 'Valute' not in data:
            self.log("Ошибка: Данные от API не получены.")
            return
            
        valutes = data['Valute']
        count = 0
        for idx, (code, info) in enumerate(valutes.items(), start=1):
            nominal = info.get('Nominal', 1)
            raw_value = info.get('Value', 0.0)
            final_rate = raw_value / nominal
            
            db_handler.save_rate(id=idx, target_currency=code, rate=final_rate)
            count += 1
            
        self.log(f"База данных обновлена. Успешно обработано валют: {count}")
        # self.refresh_combobox_values()

    def refresh_combobox_values(self):
        """Обновляет данные в ttk.Combobox на основе содержимого БД."""
        # return
        currencies = db_handler.get_all_currencies()
        self.target_entry['values'] = currencies
        if currencies:
            # Если значение ещё не выбрано, устанавливаем первую валюту по умолчанию
            if not self.target_var.get() or self.target_var.get() not in currencies:
                self.target_entry.current(0)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = CurrencyConverterApp()
    app.run()
