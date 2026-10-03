import requests

# 1. Константная переменная с URL-адресом API
API_URL = 'https://www.cbr-xml-daily.ru/daily_json.js'

def fetch_rates() -> dict:
    """Получение данных о курсе валют через API-запрос."""
    try:
        # Выполняем GET-запрос к API
        response = requests.get(API_URL)
        
        # Проверяем, что запрос прошёл успешно (статус-код 200)
        response.raise_for_status()
        
        # Возвращаем данные, автоматически преобразованные из JSON в dict
        return response.json()
        
    except requests.RequestException as e:
        print(f"Ошибка при выполнении запроса к API: {e}")
        return {}
