# Быстрый старт Database Tools

## 1. Установка зависимостей
```bash
pip install psycopg2-binary sqlalchemy
```

## 2. Настройка .env файла
Создайте `.env` файл с настройками:

```env
# OpenRouter API
OPENROUTER_API_KEY=your_api_key_here

# PostgreSQL Database  
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database
DB_USER=your_username
DB_PASSWORD=your_password
```

## 3. Тестирование
```bash
python test_db_tools.py
```

## 4. Использование
```python
from openrouter_with_db_tools import OpenRouterWithDBTools

client = OpenRouterWithDBTools()
response = client.simple_db_query("Покажи все таблицы в базе данных")
print(response)
```

## Готово! 🎉

Теперь нейронная сеть может выполнять SQL запросы к вашей PostgreSQL базе данных.
